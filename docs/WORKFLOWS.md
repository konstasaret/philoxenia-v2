# Simplified architecture and permissions

## Active runtime

Flask server-rendered pages, SQLite and local image files. `app.py` defines the public directory, journal, two intake forms and operator routes. `store.py` owns the new tables and one-way, non-destructive import. `intake_seed.py` contains initial copy and editable sample content. `operations.py` and `manage.py` provide local backup, restore, reset and operator credential management.

There is no JavaScript dependency and no outgoing request during normal operation. External stories and contact links open only when the user chooses them.

## Public flow

`Guest form or host form → saved private inquiry → confirmation`

A generated submission key makes retries idempotent, including simultaneous requests. CSRF tokens and submission keys are tied to the browser session. Contact inputs, links, required fields and size limits are checked on the server. A honeypot and 15-minute request limits reduce basic spam. A paused listing cannot accept a new inquiry referencing it; open-ended inquiries remain available.

No participant identity or account is created. The operator is the only authenticated actor.

## Operator flow

`New ↔ Contacted ↔ Arranged ↔ Closed`

These are manually editable labels with no automatic side effects. They do not reserve accommodation or notify anyone. Notes and raw submissions are visible only after operator authentication. Email and WhatsApp links open a draft/conversation; sending remains a user action.

Listings and journal entries have `draft`, `published` and `paused` states. Only published entries and their uploaded images are publicly accessible. Operators can preview hidden profiles. Exact addresses, host contacts and private notes never enter public templates.

## Permissions

| Action | Visitor | Operator |
|---|---|---|
| Read published hosts and stories | Yes | Yes |
| Submit a guest/host form | Yes, with CSRF and consent | Yes |
| Read anyone’s inquiry/contact details | No | Yes |
| Change inquiry notes/status | No | Yes |
| Add/edit/publish/pause content | No | Yes |
| Read historical records | No | Yes |

Old participant sessions use a different cookie and have no authority. Only records in the `operators` table authenticate. Passwords use PBKDF2-SHA256 with one million iterations. Cookies are HTTP-only, same-site Lax and time-limited. All mutations require CSRF. Sign-out clears the session; credential changes invalidate existing sessions through an auth version.

## Migration

Before creating intake tables in an existing database, startup snapshots it and its uploads under `.data/backups/before-intake-migration-*`. It copies only admin accounts into `operators`, listings into `listings`, and applications/host submissions/reports into `inquiries`.

All original tables remain unchanged. Original application fields are also saved as JSON in their imported inquiry. The import marker and unique legacy submission keys prevent repeated imports. New seeds insert default site copy once and do not overwrite subsequent operator edits or republish paused entries.

Earlier confirmed applications map to Arranged. Completed/declined/cancelled/withdrawn/expired map to Closed; submitted maps to New; other in-progress states map to Contacted. Original states remain available. Consent is not retroactively invented for imported records.

## Files and deployment boundaries

Uploaded images are decoded, bounded, stripped of metadata and saved as WebP under random names outside static storage. Their public route checks whether a published entry references them. Existing unused files remain in backups; no automatic file deletion is attempted.

No production host, separate admin domain, email provider, WhatsApp API, job scheduler or managed authentication service is needed for the local workflow. A separate admin domain is optional later. Public deployment requires deliberate changes to the loopback-only base URL/host configuration and a maintained production server, as documented in READINESS.md.
