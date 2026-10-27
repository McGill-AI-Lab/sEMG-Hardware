def prune_empty_old_folder(doc: dict) -> None:
    """Remove an empty folder left by the previous per-document layout."""
    try:
        (doc["out_dir"] / doc["id"]).rmdir()
    except OSError:
        pass


def index_md(root: Path, docs: list[dict], outcomes: dict[str, dict], index_file: Path) -> str:
    lines = ["# Datasheet library", "", "Original manufacturer PDFs remain the source of truth for numerical claims, equations, figures and electrical limits.", "", "| Document | PDF | Converted text | State |", "|---|---|---|---|"]
    for doc in docs:
        meta = read_json(doc["meta_path"])
        raw = doc["raw_path"]
        pdf_link = f"[PDF]({quote(Path(os.path.relpath(raw, index_file.parent)).as_posix(), safe='/')})" if raw.exists() else "—"
        links = []
        for engine in doc["converters"]:
            record = meta.get("converted", {}).get(engine, {})
            saved_path = record.get("output")
            if saved_path and safe_path(root, saved_path).exists():
                links.append(f"[{engine}]({quote(Path(os.path.relpath(safe_path(root, saved_path), index_file.parent)).as_posix(), safe='/')})")
        label = str(doc.get("title", doc["id"])).replace("|", "\\|")
        state = outcomes.get(doc["id"], {}).get("status", "not processed")
        lines.append(f"| {label} | {pdf_link} | {', '.join(links) or '—'} | {state} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Download and convert PDF datasheets from a JSON manifest")
    parser.add_argument("--manifest", default="documents.json", help="Path to JSON manifest")
    parser.add_argument("--root", help="Repository root (defaults to manifest's directory)")
    parser.add_argument("--only", action="append", help="One document ID; repeat for more")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print operations without network or writes")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--force-download", action="store_true", help="Download even when a copy already exists")
    parser.add_argument("--force-convert", action="store_true", help="Convert even when outputs match the cached PDF")
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        parser.error(f"Manifest not found: {manifest_path}")
    root = Path(args.root).expanduser().resolve() if args.root else manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    docs = validate_manifest(manifest, root)
    if args.only:
        missing = set(args.only) - {d["id"] for d in docs}
        if missing:
            parser.error(f"Unknown document ID(s): {', '.join(sorted(missing))}")
        docs = [d for d in docs if d["id"] in args.only]
    index = safe_path(root, manifest.get("defaults", {}).get("index", "docs/datasheets/INDEX.md"))
    outcomes = {}
    errors = 0
    for doc in docs:
        key, raw, out, meta_file = doc["id"], doc["raw_path"], doc["out_dir"], doc["meta_path"]
        print(f"\n[{key}] {doc['url']}", flush=True)
        if args.dry_run:
            print(f"  PDF: {raw}")
            for engine in doc["converters"]:
                print(f"  Output ({engine}): {out / (key + '_' + engine + '.md')}")
            print(f"  Converters: {', '.join(doc['converters'])}")
            outcomes[key] = {"status": "dry-run"}
            continue
        try:
            existing_meta = read_json(meta_file)
            needs_download = args.force_download or not raw.exists() or (existing_meta.get("url") not in (None, doc["url"]))
            if needs_download:
                print("  Downloading PDF...", flush=True)
                download(doc["url"], raw)
            else:
                print("  Using cached PDF", flush=True)
            with raw.open("rb") as f:
                if f.read(5) != b"%PDF-":
                    raise PipelineError("Cached file is not a PDF. Use --force-download")
            digest = file_hash(raw)
            metadata = {"id": key, "title": doc.get("title", key), "url": doc["url"],
                        "pdf": raw.relative_to(root).as_posix(), "sha256": digest,
                        "updated_utc": datetime.now(timezone.utc).isoformat(),
                        "converted": existing_meta.get("converted", {}) if existing_meta.get("sha256") == digest else {}}
            failures = []
            if not args.download_only:
                for engine in doc["converters"]:
                    target = out / f"{key}_{engine}.md"
                    prior = metadata["converted"].get(engine, {})
                    options = doc.get("options", {})
                    if migrate_old_output(root, doc, engine, prior, target, digest, options):
                        print(f"  {engine}: migrated cached output to {target.name}", flush=True)
                    prior_file = prior.get("output")
                    # Cache only the new flat output path, never a stale nested file.
                    is_cached = (not args.force_convert and prior.get("pdf_sha256") == digest
                                 and prior_file == target.relative_to(root).as_posix()
                                 and target.is_file() and prior.get("options") == options)
                    if is_cached:
                        print(f"  {engine}: cached", flush=True)
                        continue
                    try:
                        print(f"  {engine}: converting...", flush=True)
                        invoke_worker(engine, raw, target, doc["url"], doc.get("options", {}))
                        metadata["converted"][engine] = {"pdf_sha256": digest,
                            "output": target.relative_to(root).as_posix(),
                            "options": doc.get("options", {}),
                            "completed_utc": datetime.now(timezone.utc).isoformat()}
                        write_json_atomic(meta_file, metadata)
                    except (PipelineError, subprocess.CalledProcessError, OSError, ValueError) as exc:
                        failures.append(f"{engine}: {exc}")
                        print(f"  ERROR converting with {engine}: {exc}", file=sys.stderr, flush=True)
            write_json_atomic(meta_file, metadata)
            prune_empty_old_folder(doc)
            if failures:
                errors += 1
            outcomes[key] = {"status": "partial failure" if failures else "ready", "errors": failures}
        except (PipelineError, OSError, ValueError) as exc:
            errors += 1
            outcomes[key] = {"status": "failed", "errors": [str(exc)]}
            print(f"  ERROR: {exc}", file=sys.stderr, flush=True)
    if not args.dry_run:
        index.parent.mkdir(parents=True, exist_ok=True)
        # Merge index across full manifest, not only --only selection.
        all_docs = validate_manifest(manifest, root)
        index.write_text(index_md(root, all_docs, outcomes, index), encoding="utf-8")
        report_path = safe_path(root, manifest.get("defaults", {}).get("report", "docs/datasheets/latest_run.json"))
        write_json_atomic(report_path, {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "results": outcomes, "failed_documents": errors})
        print(f"\nIndex: {index}")
        print(f"Report: {report_path}")
    print(f"Done. Documents: {len(docs)}, failures: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
