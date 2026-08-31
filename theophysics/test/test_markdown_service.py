import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from markdown_service import CaptureStore


class FixtureHandler(BaseHTTPRequestHandler):
    article_text = "An ordinary article body."

    def do_GET(self):
        if self.path == "/article":
            body = f"<html><head><title>Ordinary Article</title></head><body><main><h1>Research finding</h1><p>{self.article_text}</p></main></body></html>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/javascript":
            body = b"<html><head><title>JavaScript App</title></head><body><div id='root'></div><script>render()</script></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(403)
            self.end_headers()

    def log_message(self, *_):
        pass


class MarkdownServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_article_javascript_and_blocked_provider_report(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaptureStore(Path(directory))
            result = store.preview([self.base + "/article", self.base + "/javascript", self.base + "/blocked"], allow_private=True)
            article, javascript, blocked = result["items"]
            self.assertEqual("local", article["provider"])
            self.assertIn("Research finding", article["markdown"])
            self.assertEqual("local", javascript["provider"])
            self.assertIn("JavaScript-rendered content may be incomplete", javascript["warnings"])
            self.assertEqual("failed", blocked["status"])
            self.assertIsNone(blocked["provider"])
            self.assertFalse(result["writePerformed"])
            saved = store.save([article["previewToken"]], "research-intake")
            receipt = Path(saved["saved"][0]["receiptLocation"])
            self.assertTrue(receipt.exists())
            self.assertFalse(json.loads(receipt.read_text())["canonized"])
            with self.assertRaises(FileExistsError):
                store.save([article["previewToken"]], "research-intake")
            FixtureHandler.article_text = "Changed article body."
            changed = store.preview([self.base + "/article"], allow_private=True)["items"][0]
            changed_saved = store.save([changed["previewToken"]], "research-intake")
            self.assertNotEqual(saved["saved"][0]["version"], changed_saved["saved"][0]["version"])
            self.assertTrue(Path(changed_saved["saved"][0]["receiptLocation"]).exists())


if __name__ == "__main__":
    unittest.main()
