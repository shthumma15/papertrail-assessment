# Architecture and prioritization

Papertrail uses a dependency-free Python HTTP server for both the JSON API and static frontend. The browser keeps the editing interaction local and autosaves title/content after a short debounce. The backend is the source of truth: document records, ownership, share grants, and timestamps are persisted as JSON, then loaded again after refresh.

## Data model

Each document stores an ID, title, HTML rich-text body, owner email, shared-user email list, and created/updated timestamps. The API checks the selected demo identity on every document read and mutation. Only the owner can edit, delete, or change sharing; a shared user can read. The account selector is deliberately a mock-auth convenience for reviewers, not a security boundary.

## Product choices

1. Prioritized a complete create, edit, autosave, reopen loop with modest rich-text controls.
2. Added an explicit import path for `.txt` and `.md` to make file handling visible and testable.
3. Implemented a simple, inspectable sharing model with owner/shared views and a seeded-user switcher.
4. Kept storage and dependencies minimal so reviewers can run the app without credentials, paid services, or setup friction.

Real-time collaboration, role management, document history, `.docx` conversion, and a production identity provider were intentionally deferred. A multi-user deployed service should replace the JSON file with a transactional database and replace mock identity with authenticated sessions and CSRF protection. Multiple processes writing the JSON file concurrently are not supported.
