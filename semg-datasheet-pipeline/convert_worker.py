#!/usr/bin/env python3
"""Called by uv in an isolated environment for each conversion engine."""
import argparse
from pathlib import Path


def convert(engine: str, path: str, *, formula_enrichment: bool = False) -> str:
    if engine == "markitdown":
        from markitdown import MarkItDown
        result = MarkItDown(enable_plugins=False).convert(path)
        return result.markdown

    if engine == "pymupdf4llm":
        import pymupdf4llm
        chunks = pymupdf4llm.to_markdown(path, page_chunks=True)
        return "\n\n".join(
            f"<!-- PDF page {i + 1} -->\n\n" + block.get("text", "")
            for i, block in enumerate(chunks)
        )

    if engine == "docling":
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        options = PdfPipelineOptions()
        options.do_formula_enrichment = formula_enrichment
        converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
        document = converter.convert(path).document
        return document.export_to_markdown(page_break_placeholder="\n<!-- PDF page break -->\n")

    raise ValueError("Unsupported worker engine: " + engine)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--formula-enrichment", action="store_true")
    args = ap.parse_args()
    markdown = convert(args.engine, args.input, formula_enrichment=args.formula_enrichment)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    header = f"<!-- Source: {args.url} -->\n<!-- Original PDF: {Path(args.input).name} -->\n<!-- Converter: {args.engine} -->\n<!-- Always verify engineering limits and diagrams against the PDF. -->\n\n"
    out.write_text(header + markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
