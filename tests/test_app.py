import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import server


class DocumentFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_data = server.DATA
        server.DATA = Path(cls.temp.name) / "documents.json"
        class TestHandler(server.Handler):
            def log_message(self, fmt, *args): pass
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.thread.join(timeout=2)
        server.DATA = cls.old_data
        cls.temp.cleanup()

    def call(self, method, path, user="alex@ajaia.demo", payload=None):
        raw = json.dumps(payload).encode() if payload is not None else None
        req = Request(self.base + path, data=raw, method=method, headers={"Content-Type":"application/json", "X-Demo-User":user})
        try:
            with urlopen(req) as response: return response.status, json.loads(response.read())
        except HTTPError as e: return e.code, json.loads(e.read())

    def test_create_share_readonly_and_persist(self):
        status, doc = self.call("POST", "/api/docs", payload={"title":"Review notes"})
        self.assertEqual(status, 201)
        doc_id = doc["id"]
        status, saved = self.call("PUT", f"/api/docs/{doc_id}", payload={"title":"Updated notes", "content":"<p>Useful <strong>draft</strong></p><script>alert(1)</script>"})
        self.assertEqual(status, 200)
        self.assertIn("<strong>draft</strong>", saved["content"])
        self.assertNotIn("<script>", saved["content"])
        status, _ = self.call("POST", f"/api/docs/{doc_id}/share", payload={"email":"sam@ajaia.demo"})
        self.assertEqual(status, 200)
        status, shared = self.call("GET", "/api/docs", user="sam@ajaia.demo")
        self.assertEqual(status, 200)
        self.assertEqual(shared["shared"][0]["id"], doc_id)
        status, denied = self.call("PUT", f"/api/docs/{doc_id}", user="sam@ajaia.demo", payload={"title":"Changed by reader"})
        self.assertEqual(status, 403)
        self.assertIn("read-only", denied["error"])
        # Reload the persisted JSON as a new request would after refresh/restart.
        server.load()
        status, reopened = self.call("GET", f"/api/docs/{doc_id}")
        self.assertEqual(status, 200)
        self.assertEqual(reopened["title"], "Updated notes")


if __name__ == "__main__": unittest.main()
