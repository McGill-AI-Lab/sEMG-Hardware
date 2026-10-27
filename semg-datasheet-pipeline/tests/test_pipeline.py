import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'doc_pipeline.py'
spec = importlib.util.spec_from_file_location('doc_pipeline', SCRIPT)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Tests(unittest.TestCase):
    def test_url_validation(self):
        self.assertTrue(p.is_public_https('https://www.ti.com/lit/ds/symlink/ads1298.pdf'))
        for url in ['http://www.ti.com/file.pdf', 'https://localhost/a', 'https://127.0.0.1/a', 'file:///etc/passwd', 'https://user:pass@example.com/a']:
            self.assertFalse(p.is_public_https(url))

    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertTrue(p.safe_path(root, 'docs/datasheets/a.pdf').is_relative_to(root))
            for x in ['../a', '/etc/passwd', 'foo/../../b', 'foo\\bar']:
                with self.assertRaises(p.PipelineError):
                    p.safe_path(root, x)

    def test_manifest_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            valid = {'schema': 1, 'documents': [{'id':'ADS1298','url':'https://www.ti.com/lit/ds/symlink/ads1298.pdf','converters':['markitdown','pymupdf4llm']}]}
            docs = p.validate_manifest(valid, root)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]['folder'], 'general')
            bad = json.loads(json.dumps(valid))
            bad['documents'][0]['folder'] = '../../bad'
            with self.assertRaises(p.PipelineError):
                p.validate_manifest(bad, root)

    def test_dry_run_creates_no_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            m = root / 'documents.json'
            m.write_text(json.dumps({'schema': 1, 'documents': [{'id':'ADS1298','url':'https://www.ti.com/lit/ds/symlink/ads1298.pdf','converter':'pymupdf4llm'}]}))
            ret = p.main(['--manifest', str(m), '--root', str(root), '--dry-run'])
            self.assertEqual(ret, 0)
            self.assertEqual(set(root.rglob('*')), {m})

    def test_download_invalid_pdf_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'x.pdf'
            out.write_bytes(b'%PDF-1.4\nOLD\n')
            class FakeResponse:
                url = 'https://example.com/a.pdf'
                headers = {'Content-Length': '123'}
                def __enter__(self): return self
                def __exit__(self,*a): return False
                def read(self,n): return b'<html>not pdf</html>' if not hasattr(self, 'returned') else b''
            f = FakeResponse()
            def read(n):
                if hasattr(f,'returned'): return b''
                f.returned = True
                return b'<html>not pdf</html>'
            f.read = read
            class Opener:
                def open(self,*a,**kw): return f
            with patch.object(p, 'build_opener', return_value=Opener()):
                with self.assertRaises(p.PipelineError):
                    p.download('https://example.com/a.pdf', out, attempts=1)
            self.assertEqual(out.read_bytes(), b'%PDF-1.4\nOLD\n')


if __name__ == '__main__':
    unittest.main()


class PipelineEndToEnd(unittest.TestCase):
    def test_cached_download_and_conversions_and_index(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            manifest = root/'manifest.json'
            manifest.write_text(json.dumps({'schema':1,'documents':[{'id':'ADS1298','url':'https://www.ti.com/lit/ds/symlink/ads1298.pdf','folder':'components','converters':['pymupdf4llm','markitdown']}]}))
            originals = root/'docs/datasheets/originals/components/ADS1298.pdf'
            originals.parent.mkdir(parents=True)
            originals.write_bytes(b'%PDF-1.4\n' + b'X'*100)
            calls=[]
            def fake_converter(engine,pdf,out,url,options):
                calls.append(engine)
                out.parent.mkdir(parents=True,exist_ok=True)
                out.write_text('# example document from '+engine)
            with patch.object(p,'invoke_worker',side_effect=fake_converter):
                self.assertEqual(p.main(['--manifest',str(manifest),'--root',str(root)]),0)
                self.assertEqual(calls,['pymupdf4llm','markitdown'])
                self.assertEqual(p.main(['--manifest',str(manifest),'--root',str(root)]),0)
                self.assertEqual(calls,['pymupdf4llm','markitdown'])
                self.assertEqual(p.main(['--manifest',str(manifest),'--root',str(root),'--force-convert']),0)
                self.assertEqual(calls,['pymupdf4llm','markitdown','pymupdf4llm','markitdown'])
            self.assertTrue((root/'docs/datasheets/INDEX.md').exists())
            metadata=json.loads((root/'docs/datasheets/metadata/components/ADS1298.json').read_text())
            self.assertEqual(metadata['sha256'],p.file_hash(originals))
