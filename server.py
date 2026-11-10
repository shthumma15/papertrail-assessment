"""Small, dependency-free collaborative document demo for the Ajaia assessment."""
from __future__ import annotations

import html
import json
import os
import re
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("DOCS_DATA", ROOT / "data" / "documents.json"))
USERS = {"alex@ajaia.demo": "Alex Morgan", "sam@ajaia.demo": "Sam Lee", "jules@ajaia.demo": "Jules Kim"}
MAX_BODY = 2_000_000


class Sanitizer(HTMLParser):
    ALLOWED = {"p", "br", "strong", "b", "em", "i", "u", "h1", "h2", "h3", "ul", "ol", "li", "blockquote", "a"}
    VOID = {"br"}
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []
    def handle_starttag(self, tag, attrs):
        if tag not in self.ALLOWED: return
        if tag == "a":
            href = dict(attrs).get("href", "")
            if re.match(r"^https?://", href): self.out.append(f'<a href="{html.escape(href, quote=True)}" rel="nofollow noopener">')
            else: self.out.append("<a>")
        else: self.out.append(f"<{tag}>")
    def handle_endtag(self, tag):
        if tag in self.ALLOWED and tag not in self.VOID: self.out.append(f"</{tag}>")
    def handle_data(self, data): self.out.append(html.escape(data))
    def handle_entityref(self, name): self.out.append(f"&{name};")
    def handle_charref(self, name): self.out.append(f"&#{name};")


def clean(content: str) -> str:
    parser = Sanitizer(); parser.feed(content[:500_000]); parser.close()
    return "".join(parser.out)


def load():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if DATA.exists():
        try: return json.loads(DATA.read_text())
        except (json.JSONDecodeError, OSError): pass
    return []


def save(docs):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(docs, ensure_ascii=False, indent=2))
    tmp.replace(DATA)


class Handler(BaseHTTPRequestHandler):
    server_version = "Papertrail/1.0"
    def log_message(self, fmt, *args): pass
    def send_json(self, status, value):
        raw = json.dumps(value).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(raw)
    def body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > MAX_BODY: raise ValueError("Request is too large")
        return json.loads(self.rfile.read(size) or b"{}")
    def user(self):
        email = self.headers.get("X-Demo-User", "alex@ajaia.demo")
        return email if email in USERS else "alex@ajaia.demo"
    def visible(self, doc, user): return doc["owner"] == user or user in doc["sharedWith"]
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/users": return self.send_json(200, [{"email": e, "name": n} for e,n in USERS.items()])
        if path.startswith("/api/docs"):
            docs, user = load(), self.user()
            if path == "/api/docs":
                mine = [dict(d, access="owner") for d in docs if d["owner"] == user]
                shared = [dict(d, access="shared") for d in docs if user in d["sharedWith"] and d["owner"] != user]
                return self.send_json(200, {"owned": sorted(mine,key=lambda d:d["updatedAt"],reverse=True), "shared": sorted(shared,key=lambda d:d["updatedAt"],reverse=True)})
            doc = next((d for d in docs if path == "/api/docs/"+d["id"]), None)
            if not doc: return self.send_json(404,{"error":"Document not found"})
            if not self.visible(doc,user): return self.send_json(403,{"error":"You do not have access to this document"})
            return self.send_json(200,doc)
        return self.send_json(404,{"error":"Not found"})
    def do_POST(self):
        path = urlparse(self.path).path
        try: payload = self.body()
        except (ValueError,json.JSONDecodeError): return self.send_json(400,{"error":"Invalid or oversized request"})
        docs, user = load(), self.user()
        if path == "/api/docs":
            title = str(payload.get("title", "Untitled document")).strip()[:120] or "Untitled document"
            doc = {"id":str(uuid.uuid4()),"title":title,"content":"<p></p>","owner":user,"sharedWith":[],"createdAt":datetime.now(timezone.utc).isoformat(),"updatedAt":datetime.now(timezone.utc).isoformat()}
            docs.append(doc); save(docs); return self.send_json(201,doc)
        if path == "/api/upload":
            name = str(payload.get("name", "upload.txt"))[:120]
            if Path(name).suffix.lower() not in {".txt", ".md"}: return self.send_json(415,{"error":"Please upload a .txt or .md file"})
            raw = str(payload.get("text", ""))[:100_000]
            # Import plain text as paragraphs; HTML is escaped before the editor sees it.
            blocks = "".join("<p>"+html.escape(line)+"</p>" for line in raw.splitlines() if line.strip()) or "<p></p>"
            doc = {"id":str(uuid.uuid4()),"title":Path(name).stem[:120] or "Imported document","content":blocks,"owner":user,"sharedWith":[],"createdAt":datetime.now(timezone.utc).isoformat(),"updatedAt":datetime.now(timezone.utc).isoformat()}
            docs.append(doc); save(docs); return self.send_json(201,doc)
        match = re.fullmatch(r"/api/docs/([^/]+)/share",path)
        if match:
            doc = next((d for d in docs if d["id"] == match.group(1)),None)
            if not doc: return self.send_json(404,{"error":"Document not found"})
            if doc["owner"] != user: return self.send_json(403,{"error":"Only the owner can manage access"})
            target = str(payload.get("email", "")).strip().lower()
            if target not in USERS: return self.send_json(400,{"error":"Choose a seeded demo user"})
            if target != user and target not in doc["sharedWith"]: doc["sharedWith"].append(target)
            doc["updatedAt"] = datetime.now(timezone.utc).isoformat(); save(docs)
            return self.send_json(200,doc)
        return self.send_json(404,{"error":"Not found"})
    def do_PUT(self):
        match = re.fullmatch(r"/api/docs/([^/]+)",urlparse(self.path).path)
        if not match: return self.send_json(404,{"error":"Not found"})
        try: payload = self.body()
        except (ValueError,json.JSONDecodeError): return self.send_json(400,{"error":"Invalid or oversized request"})
        docs,user=load(),self.user(); doc=next((d for d in docs if d["id"]==match.group(1)),None)
        if not doc: return self.send_json(404,{"error":"Document not found"})
        if not self.visible(doc,user): return self.send_json(403,{"error":"You do not have access to this document"})
        if doc["owner"] != user: return self.send_json(403,{"error":"Shared documents are read-only in this demo"})
        if "title" in payload: doc["title"] = str(payload["title"]).strip()[:120] or "Untitled document"
        if "content" in payload: doc["content"] = clean(str(payload["content"]))
        doc["updatedAt"] = datetime.now(timezone.utc).isoformat(); save(docs); return self.send_json(200,doc)
    def do_DELETE(self):
        match=re.fullmatch(r"/api/docs/([^/]+)",urlparse(self.path).path)
        if not match:return self.send_json(404,{"error":"Not found"})
        docs,user=load(),self.user(); doc=next((d for d in docs if d["id"]==match.group(1)),None)
        if not doc:return self.send_json(404,{"error":"Document not found"})
        if doc["owner"]!=user:return self.send_json(403,{"error":"Only the owner can delete this document"})
        save([d for d in docs if d["id"]!=doc["id"]]); return self.send_json(200,{"ok":True})
    def do_HEAD(self):
        if urlparse(self.path).path=="/":self.send_response(200);self.end_headers()
        else:self.send_response(404);self.end_headers()
    def do_OPTIONS(self): self.send_response(204);self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Headers","Content-Type, X-Demo-User");self.send_header("Access-Control-Allow-Methods","GET,POST,PUT,DELETE,OPTIONS");self.end_headers()
    def do_PATCH(self): self.send_json(405,{"error":"Method not allowed"})

    def do_GET_static(self): pass

    def translate_path(self, path):
        return str(ROOT / "public" / ("index.html" if path == "/" else path.lstrip("/")))


if __name__ == "__main__":
    from http.server import SimpleHTTPRequestHandler
    class AppHandler(Handler, SimpleHTTPRequestHandler):
        def do_GET(self):
            if urlparse(self.path).path.startswith("/api/"): return Handler.do_GET(self)
            return SimpleHTTPRequestHandler.do_GET(self)
        def do_HEAD(self):
            if urlparse(self.path).path.startswith("/api/"): return Handler.do_HEAD(self)
            return SimpleHTTPRequestHandler.do_HEAD(self)
    os.chdir(ROOT / "public")
    port=int(os.environ.get("PORT",8000))
    print(f"Papertrail running at http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0",port),AppHandler).serve_forever()
