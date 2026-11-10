# AI workflow note

I used ChatGPT as a coding assistant to turn the assignment into a focused feature plan, scaffold the initial server and UI, and iterate on the implementation. The main acceleration came from generating the first pass of the API, editor layout, seeded-account flow, and documentation together rather than hand-writing boilerplate in sequence.

I kept product decisions in my hands: a single-owner editor with read-only shares, `.txt`/`.md` import, and a dependency-free local JSON store fit the timebox and make the demo easy to run. I deferred real-time co-editing, full Markdown conversion, `.docx`, production authentication, and database hosting. I added server-side rich-text allowlisting and access checks as guardrails rather than trusting the client.

I reviewed and adjusted the generated code, then used the automated HTTP-level test to check document creation, persistence through reload from the data file, sharing visibility, read-only enforcement, and unsafe HTML stripping. The test is a targeted check, not a substitute for a full browser and deployment review. Before submission, manually exercise the editor, import, and account-switching flows in a browser and verify the live deployment URL and shared demo credentials.
