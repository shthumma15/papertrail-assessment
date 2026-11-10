# AI workflow note

I used ChatGPT as a coding assistant to turn the assignment into a focused feature plan, scaffold the initial server and UI, and iterate on the implementation. The main acceleration came from generating the first pass of the API, editor layout, seeded-account flow, and documentation together rather than hand-writing boilerplate in sequence.

I kept product decisions in my hands: a single-owner editor with read-only shares, `.txt`/`.md` import, and a dependency-free local JSON store fit the timebox and make the demo easy to run. I deferred real-time co-editing, full Markdown conversion, `.docx`, production authentication, and database hosting. I added server-side rich-text allowlisting and access checks as guardrails rather than trusting the client.

I reviewed and revised the AI-generated UI: I removed the inactive three-dot control, made the “My workspace” breadcrumb return to the workspace, and replaced generic footer slogans with useful import and sharing information. I also kept the scope focused on the requested editing, import, and sharing flows rather than adding real-time co-editing or production authentication.

I manually checked the main app flows. The included automated test passed during development; it covers document saving, sharing access, read-only enforcement, and content sanitization. The deployed app uses seeded demo accounts and JSON-file storage, so it is a scoped prototype rather than a production collaboration system. Render’s free service may reset that local data after it spins down. With another 2–4 hours, I would add durable database storage and real authentication.
