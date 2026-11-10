# Papertrail

A small, full-stack collaborative document editor built for the Ajaia AI-Native Full Stack Developer assignment.

## Run locally

Requirements: Python 3.10 or newer. No third-party packages or paid services are required.

```bash
python server.py
```

Open [http://localhost:8000](http://localhost:8000). Documents are stored in `data/documents.json` and survive refreshes and server restarts. Set `PORT` to change the listening port, or `DOCS_DATA` to choose another writable JSON data file.

## Try the main flows

1. Create a document, rename it, and use the toolbar for bold, italic, underline, headings, and lists. Changes save automatically.
2. Import a `.txt` or `.md` file from the welcome screen or editor toolbar. Files are limited to 100 KB; imported text becomes editable paragraphs.
3. Open **Share**, invite Sam or Jules, then switch accounts from the sidebar to see the document in **Shared with me**. Shared access is read-only.
4. Refresh the page: documents, content, and share grants remain available.

The account selector simulates authentication with three seeded users: Alex (`alex@ajaia.demo`), Sam (`sam@ajaia.demo`), and Jules (`jules@ajaia.demo`). This is a demo identity model, not production authentication.

## Automated test

```bash
python -m unittest discover -s tests -v
```

## Deployment

The app listens on `0.0.0.0:$PORT`, so it can run on a Python web host that supports a persistent writable disk. Configure the start command as `python server.py` and mount persistent storage for `DOCS_DATA` (for example, `/var/data/documents.json`). A host with ephemeral storage will lose data when its instance is replaced. The assessment asks for a live product URL; https://papertrail-assessment.onrender.com/

## Scope and limitations

- A single document owner can edit; invited demo users can read. There is no simultaneous editing, conflict resolution, or real sign-in.
- Only UTF-8 `.txt` and `.md` are imported. Markdown is imported as literal text paragraphs; full Markdown rendering and `.docx` conversion are out of scope.
- The local JSON store is appropriate for a small single-instance demo, not concurrent multi-instance production use.
- Document content is sanitized server-side to a small rich-text allowlist before storage.
