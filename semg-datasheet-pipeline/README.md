# sEMG datasheet pipeline

One manifest controls **PDF URLs**, **folders**, and **converter choice**. The pipeline downloads original PDFs, converts them to searchable Markdown, caches unchanged outputs, creates a Markdown index and JSON provenance records, and continues if one document or converter fails.

## Mac / Codex setup (once)

1. Download `semg-datasheet-pipeline.zip` and extract it into the **root** of your copied `sEMG-Hardware-Codex` repository. Keep the folder name `semg-datasheet-pipeline`.
2. Open Terminal and go to your repository root:

   ```bash
   cd ~/Documents/Projects/Hardware/sEMG-Hardware-Codex
   ```

3. Inspect `semg-datasheet-pipeline/documents.json`; change or remove unwanted entries. Each document has a stable `id`, an HTTPS `url`, a destination `folder`, and a `converters` list. The sample manifest has 13 documents matching your sEMG project research needs.
4. Preview without downloading anything:

   ```bash
   python3 semg-datasheet-pipeline/doc_pipeline.py --manifest semg-datasheet-pipeline/documents.json --root . --dry-run
   ```

5. Try the ADS1298 datasheet first:

   ```bash
   python3 semg-datasheet-pipeline/doc_pipeline.py --manifest semg-datasheet-pipeline/documents.json --root . --only ADS1298
   ```

6. Process all configured documents with the one-command wrapper:

   ```bash
   bash semg-datasheet-pipeline/run.sh
   ```

   You can pass optional flags to this command, for example `bash semg-datasheet-pipeline/run.sh --only SBAA188` or `bash semg-datasheet-pipeline/run.sh --dry-run`.

**Prerequisite**: `uv` on your shell PATH. You already installed `uvx`; `uv` is included in the same installation. Converters are installed automatically and cached **as isolated environments** by `uv run`, not in your system Python. The first use of Docling or Marker may download significant dependencies or models. On a 16-GB Mac, run sequentially (the script already does) and prefer PyMuPDF4LLM.

## Output layout

```text
sEMG-Hardware-Codex/
├── semg-datasheet-pipeline/
│   ├── documents.json                # Only file you normally edit
│   ├── doc_pipeline.py
│   ├── convert_worker.py
│   └── README.md
└── docs/
    └── datasheets/
        ├── originals/
        │   ├── components/ADS1298.pdf
        │   └── ti-app-notes/SBAA188.pdf
        ├── processed/
        │   ├── components/ADS1298/pymupdf4llm.md
        │   └── ti-app-notes/SBAA188/
        │       ├── pymupdf4llm.md
        │       └── docling.md
        ├── metadata/
        │   └── components/ADS1298.json
        ├── INDEX.md
        └── latest_run.json
```

The original PDFs are **never overwritten by conversion**. Re-running the pipeline skips existing PDFs and Markdown when the SHA-256 hash matches recorded metadata. Use `--force-convert` to re-run the selected converters or `--force-download` to refresh the source PDFs. If a source URL changes between runs, the corresponding PDF will be refreshed. The `--download-only` mode does not convert PDFs.

## Change a converter or add a document

Inside `documents.json`, examples:

```json
{"id": "ADS1298", "title": "ADS1298 datasheet", "folder": "components", "url": "https://www.ti.com/lit/ds/symlink/ads1298.pdf", "converters": ["pymupdf4llm"]}
```

A dual extraction:

```json
{"id": "SBAA188", "title": "RLD and CMRR note", "folder": "ti-app-notes", "url": "https://www.ti.com/lit/pdf/SBAA188", "converters": ["pymupdf4llm", "docling"]}
```

Supported converters and their behavior:

| Converter | Best for | Notes |
|---|---|---|
| `pymupdf4llm` | Primary local technical PDF extraction | Adds `<!-- PDF page N -->` markers using page chunks |
| `markitdown` | Lightweight general text extraction | No reliable page markers in basic converter |
| `docling` | Difficult table layouts | Adds page-break markers but not precise per-item page citation; `"options":{"docling_formula_enrichment":true}` can turn on optional formula models; this can be slow |
| `marker` | Experimental fallback for difficult pages | Runs fast mode via its CLI and preserves its generated asset folder; `"options":{"marker_disable_ocr":false}` enables OCR/VLM functionality, possibly heavy on Mac |

MarkItDown, PyMuPDF4LLM and Docling use the official Python interfaces in isolated `uv` environments. Marker uses its CLI. All default to **local processing** without a commercial cloud API. Some engines download model weights from remote hosts on first use; consult their documentation if the machine must run offline. Manufacturer URLs are used only for downloads and references.

## Troubleshooting

- **`uv is not installed`** — check `uv --version`, or use the installer at https://docs.astral.sh/uv/getting-started/installation/.
- **HTTP 403 / bot protection / redirect not a PDF** — download that PDF manually with a browser into the printed `originals/...` target and rerun; the script will use the valid local file.
- **`uv run` fails** — check the converter's installation errors in Terminal. Restart with `--only <ID>` after correcting them.
- **Docling is slow** — remove `docling` from that document's `converters` array; PyMuPDF4LLM remains a fast baseline.
- **Missing symbols, tables or pin diagrams** — inspect the original PDF. Converted Markdown is for search and retrieval, not authoritative engineering review.
- **Need a different output tree** — change `defaults.originals`, `defaults.processed`, `defaults.metadata` and each entry's `folder`.

## Validation and limitations

- Downloads use HTTPS, size limits (75 MiB), temporary files and a PDF signature check. Only add trusted manufacturer URLs. This is not a hardened downloader for arbitrary untrusted manifests.
- Cached PDFs are validated for the PDF signature but not syntactically inspected until a converter reads them.
- The script does **not** automatically evaluate text extraction quality, validate numerical units or resolve circuit diagrams into structured netlists.
- For critical specifications (ADS1298 noise versus gain/data rate, CMRR, reference limits, regulator output conditions), check the original PDF page before acting on an engineering recommendation.
- Exact converter output and PDF revisions can change over time; JSON metadata records a PDF SHA-256 but not the full Python environment lock. For strict reproducibility, pin package versions in `ENGINES` in `doc_pipeline.py`.

## Test the script

```bash
python3 -m unittest discover -s semg-datasheet-pipeline/tests -v
```
