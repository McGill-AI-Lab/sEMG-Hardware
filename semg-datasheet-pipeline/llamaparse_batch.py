#!/usr/bin/env python3
"""Batch LlamaParse v2 PDF extraction for the sEMG datasheet manifest.

Requires: llama-cloud>=2.8, pypdf, certifi. No paid plan required if
LlamaCloud project remains on Free; API enforces its own actual balance.
"""
import argparse
import hashlib
import json
import os
import ssl
import sys
import tempfile
import urllib.request
from pathlib import Path

SKIP_IDS = {"ESP32-S3-TRM"}
PRIORITY_PLUS = [
    "ADS1298", "LP2985", "TLV755P", "ADS1298-EVM",
    "ESP32-S3-WROOM-1", "SBAA188", "SBAA196",
]
RATE = {"agentic": 10, "agentic_plus": 45}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}.", delete=False) as f:
        f.write(content)
        temporary = Path(f.name)
    temporary.replace(path)


def to_data(obj):
    if hasattr(obj, "model_dump"):
        return to_data(obj.model_dump(mode="json", exclude_none=True))
    if isinstance(obj, dict):
        return {str(k): to_data(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_data(x) for x in obj]
    return obj


def download_pdf(url, path):
    import certifi
    context = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "sEMG-Datasheet-Pipeline/1.0"})
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=".pdf-", delete=False) as out:
        tmp = Path(out.name)
        try:
            with urllib.request.urlopen(req, timeout=100, context=context) as response:
                while True:
                    buf = response.read(1024 * 1024)
                    if not buf:
                        break
                    out.write(buf)
                    if out.tell() > 75 * 1024 * 1024:
                        raise ValueError("PDF larger than 75 MiB")
            with tmp.open("rb") as check:
                if not check.read(1024).lstrip().startswith(b"%PDF-"):
                    raise ValueError("Downloaded content is not a PDF")
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)


def choose_tiers(entries, strategy, budget):
    # entries: dicts with id, pages, etc. All pages conservatively counted.
    if strategy == "agentic_plus":
        tiers = {e["id"]: "agentic_plus" for e in entries}
    elif strategy == "agentic":
        tiers = {e["id"]: "agentic" for e in entries}
    else:
        total_plus = sum(e["pages"] * 45 for e in entries)
        tiers = {e["id"]: ("agentic_plus" if total_plus <= budget else "agentic")
                 for e in entries}
        if total_plus > budget:
            for doc_id in PRIORITY_PLUS:
                target = next((e for e in entries if e["id"] == doc_id), None)
                if target is None:
                    continue
                estimate = sum(e["pages"] * RATE[tiers[e["id"]]] for e in entries)
                if estimate + target["pages"] * 35 <= budget:
                    tiers[doc_id] = "agentic_plus"
    projected = sum(e["pages"] * RATE[tiers[e["id"]]] for e in entries)
    if projected > budget:
        raise ValueError(
            f"Estimated {projected:,} credits exceeds local budget {budget:,}. "
            "Use --strategy agentic or increase --budget only if your credits support it."
        )
    return tiers, projected


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parent / "documents.json")
    ap.add_argument("--only", action="append", default=[], metavar="DOC_ID")
    ap.add_argument("--strategy", choices=["auto", "agentic", "agentic_plus"], default="auto")
    ap.add_argument("--budget", type=int, default=29000,
                    help="Local projected-credit ceiling; not a live account-balance check")
    ap.add_argument("--download-missing", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="Plan only; never call LlamaCloud")
    args = ap.parse_args()
    if args.budget <= 0 or args.budget > 30000:
        ap.error("Budget must be between 1 and 30000 (your stated award)")

    from pypdf import PdfReader
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = args.root.resolve()
    originals = root / manifest["defaults"]["originals"]
    processed = root / manifest["defaults"]["processed"]
    meta_dir = root / manifest["defaults"]["metadata"]
    selected = set(args.only)
    entries = []
    failures = []
    for doc in manifest["documents"]:
        id_ = doc["id"]
        if id_ in SKIP_IDS or (selected and id_ not in selected):
            continue
        folder = doc["folder"]
        pdf = originals / folder / f"{id_}.pdf"
        if not pdf.exists() and args.download_missing:
            print(f"Downloading {id_}...", flush=True)
            try:
                download_pdf(doc["url"], pdf)
            except Exception as exc:
                failures.append(f"{id_}: download failed: {exc}")
                continue
        if not pdf.exists():
            failures.append(f"{id_}: missing {pdf} (use --download-missing)")
            continue
        try:
            pages = len(PdfReader(str(pdf), strict=False).pages)
        except Exception as exc:
            failures.append(f"{id_}: invalid PDF: {exc}")
            continue
        if pages < 1:
            failures.append(f"{id_}: empty PDF")
            continue
        entries.append({"id": id_, "folder": folder, "pdf": pdf,
                        "pages": pages, "sha256": digest(pdf), "title": doc.get("title", id_)})
    for problem in failures:
        print("ERROR:", problem, file=sys.stderr)
    if failures:
        raise SystemExit("Fix missing/invalid PDFs before submitting any paid-credit parse jobs.")
    if not entries:
        ap.error("No matching documents found")

    # Successful local outputs are skipped to avoid unnecessary re-billing.
    pending = []
    for entry in entries:
        base = processed / entry["folder"] / f'{entry["id"]}_llamaparse'
        record = meta_dir / entry["folder"] / f'{entry["id"]}_llamaparse.json'
        entry.update(md=base.with_suffix(".md"), json=base.with_suffix(".json"), record=record)
        if record.exists() and entry["md"].exists() and entry["json"].exists():
            try:
                old = json.loads(record.read_text(encoding="utf-8"))
                if old.get("sha256") == entry["sha256"] and old.get("status") == "success":
                    print(f'SKIP cached: {entry["id"]} ({old.get("tier")})')
                    continue
            except (OSError, ValueError):
                pass
        pending.append(entry)

    tiers, projected = choose_tiers(pending, args.strategy, args.budget)
    print(f"\n{len(pending)} PDFs queued; projected maximum {projected:,} credits "
          f"(local ceiling {args.budget:,}).")
    for entry in pending:
        tier = tiers[entry["id"]]
        print(f'  {entry["id"]:25} {entry["pages"]:4} pp  {tier:12} '
              f'~{entry["pages"] * RATE[tier]:,} credits')
    print("Skipped permanently:", ", ".join(sorted(SKIP_IDS)))
    if args.dry_run:
        print("Dry run: no API requests made.")
        return
    if not os.environ.get("LLAMA_CLOUD_API_KEY"):
        raise SystemExit("Set LLAMA_CLOUD_API_KEY first; see README")

    from llama_cloud import LlamaCloud
    client = LlamaCloud()
    for index, entry in enumerate(pending, 1):
        doc_id = entry["id"]
        tier = tiers[doc_id]
        print(f"\n[{index}/{len(pending)}] Uploading {doc_id} ({tier})...", flush=True)
        file_id = None
        try:
            uploaded = client.files.create(file=str(entry["pdf"]), purpose="parse")
            file_id = uploaded.id
            result = client.parsing.parse(
                file_id=file_id, tier=tier, version="latest",
                output_options={"markdown": {"tables": {
                    "output_tables_as_markdown": False,
                    "merge_continued_tables": True,
                }}},
                expand=["markdown", "items"],
            )
            markdown_pages = list(result.markdown.pages if result.markdown else [])
            item_pages = list(result.items.pages if result.items else [])
            failed_pages = [p.page_number for p in markdown_pages if not getattr(p, "success", True)]
            if failed_pages or not markdown_pages or len(markdown_pages) != entry["pages"]:
                raise RuntimeError(f"Incomplete output: {len(markdown_pages)}/{entry['pages']} "
                                   f"pages, failed={failed_pages}. No success cache written.")
            blocks = [f'# {entry["title"]}', f'<!-- Original PDF: {entry["pdf"].name} -->']
            for p in markdown_pages:
                blocks += [f'\n<!-- PDF page {p.page_number} -->\n', p.markdown or '']
            md_text = "\n\n".join(blocks).rstrip() + "\n"
            raw_items = [to_data(page) for page in item_pages]
            table_count = sum(1 for page in item_pages if getattr(page, "success", True)
                              for item in getattr(page, "items", []) if getattr(item, "type", None) == "table")
            sidecar = {"document_id": doc_id, "source_pdf": str(entry["pdf"].relative_to(root)),
                       "tier": tier, "sha256": entry["sha256"], "pages": entry["pages"],
                       "tables_detected": table_count, "items_pages": raw_items}
            atomic_text(entry["json"], json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n")
            atomic_text(entry["md"], md_text)
            record = {"id": doc_id, "sha256": entry["sha256"], "tier": tier,
                      "status": "success", "page_count": len(markdown_pages),
                      "tables_detected": table_count, "job_id": getattr(getattr(result, "job", None), "id", None)}
            atomic_text(entry["record"], json.dumps(record, indent=2) + "\n")
            print(f"  Saved {entry['md'].relative_to(root)}")
            print(f"  Saved {entry['json'].relative_to(root)} ({table_count} tables)")
        except Exception as exc:
            print(f"FAILED on {doc_id}: {exc}", file=sys.stderr)
            print("Stopping. Completed files are cached locally; rerun to resume.", file=sys.stderr)
            raise SystemExit(1) from exc
        finally:
            if file_id:
                try:
                    client.files.delete(file_id)
                except Exception as exc:
                    print(f"Warning: could not delete remote source file {file_id}: {exc}",
                          file=sys.stderr)
    print("\nDone. Output tables are retained as HTML in Markdown and as typed items in JSON.")


if __name__ == "__main__":
    main()
