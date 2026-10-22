# Public-launch readiness — simplified Open Estia

**Works locally:** public host directory and builder journal; guest and host forms; private operator inbox; email/WhatsApp launch links; editable listings, free benefits, photos, stories and copy; persistent local storage; backup/restore; preserved historical records.

**Current limitations:** local-only development server, shared demo operator credentials, fictional host profiles, third-party photo permissions unverified, final privacy/operator details not supplied, and browser-based desktop/mobile verification pending. The source is prepared for the user-selected GitHub repository. The website has not been deployed and no messages have been sent.

Guest/host accounts, automated booking, capacity management, verification/reset email, reminders and offer expiry are intentionally removed. They are not missing launch integrations for this model.

## 1. Domain and hosting

| Item | Current status | You supply/decide | Connect/change | Verify | Blocks public launch? |
|---|---|---|---|---|---|
| Domain and DNS | Needs decision | Choose an available name and hosting provider | Purchase/configure only when separately authorized | DNS points to chosen host | Yes for a custom domain; provider URL can work |
| Hosting and HTTPS | Needs connection | A host capable of Python and persistent disk | Maintained Python, WSGI server, reverse proxy and HTTPS; change hardcoded loopback binding/trusted hosts/base URL guard deliberately | Guest and operator flows over HTTPS with valid certificate | Yes |
| Admin location | Ready locally | Same site at /admin or later a separate domain | Existing private /admin works; a separate domain adds cookie, host and CSRF configuration | Public visitors cannot read or mutate admin records | Separate domain is optional |
| Public URLs | Needs connection | Final canonical URL | OPEN_ESTIA_BASE_URL plus allowed-host and URL-validation changes; OPEN_ESTIA_PORT for server configuration | No localhost links in deployed routes | Yes |

## 2. Data and files

| Item | Current status | You supply/decide | Connect/change | Verify | Blocks? |
|---|---|---|---|---|---|
| Database | Ready locally | Single persistent server vs multiple instances | SQLite is suitable for a small single-instance manual pilot with durable disk. Use PostgreSQL and port the migration if using multiple instances or ephemeral/serverless storage | Save, restart and recover an inquiry | Durable storage: yes; PostgreSQL: optional |
| Migration | Ready locally | Which records are real and should transfer | Copy the DB through backup/restore; import preserves old tables and notes. Remove sample records deliberately before real launch | Record counts, content comparisons and admin privacy | Yes |
| Images | Ready locally | Persistent disk or a future object store | Keep uploads outside public static paths; preserve guarded image serving for draft records | Public image works only for published entries | Yes |
| Backups | Ready locally | Recovery frequency and storage location | Schedule encrypted backups off the server; retain database and uploads together | Restore to a clean environment and inspect data/media | Yes |
| Legacy retention | Needs decision | Retention/deletion policy for old accounts and records | Decide whether to retain the private archive; remove unnecessary legacy data after backup and review | Confirm intended records only | Yes before handling real data long-term |

## 3. Accounts and communication

| Item | Current status | You supply/decide | Connect/change | Verify | Blocks? |
|---|---|---|---|---|---|
| Operator credentials | Ready locally | Real operator email and a unique strong password | manage.py operator --email ADDRESS prompts securely and invalidates sessions; replace sample credentials | Old password and session fail; new credentials work | Yes |
| Sessions | Needs connection | Session lifetime and production secret storage | OPEN_ESTIA_SECRET_KEY, OPEN_ESTIA_SESSION_HOURS, OPEN_ESTIA_COOKIE_SECURE=1 with HTTPS; don't share secrets in source | Secure/HttpOnly/SameSite cookie and expiry | Yes |
| Participant accounts | Ready locally | No accounts required | Nothing to connect | Both forms work in a fresh browser | No |
| Manual email / WhatsApp | Ready locally | Monitored mailbox and your own WhatsApp account; support email in Website settings | Open email/WhatsApp buttons use the visitor's supplied contact information; sending remains manual | Open each link and deliberately send a test message yourself | A working follow-up channel: yes |
| Automated email / WhatsApp API | Needs decision | Whether ever wanted | Not used. No provider, sender-domain verification, webhooks or API keys required for this scope | Not applicable unless introduced | No |

## 4. Operations

| Item | Current status | You supply/decide | Connect/change | Verify | Blocks? |
|---|---|---|---|---|---|
| Daily review | Needs decision | Who checks the inbox and response expectations | Manual status/notes and personal follow-up | Submit both forms and confirm an operator follows up | Yes |
| Security checks | Ready locally | Deployment review owner | CSRF, auth, input limits, no participant access, hidden private fields, validated/re-encoded images and basic rate limits are implemented | Run the current tests, then review proxy and production configuration | Deployment review: yes |
| Spam controls | Needs connection | Expected audience and abuse tolerance | Keep server validation; review trusted proxy/IP handling and adjust limits or add CAPTCHA only if needed | Rate-limit/spam tests on deployed host | Basic protection: yes; extra services optional |
| Monitoring | Needs connection | Alert recipient and retention | Production process supervision, private logs, error monitoring, uptime checks and backup alerts | Simulate a failed request/restart and verify recovery/alerts | Yes |
| Schedulers | Ready locally | No booking scheduler needed | No reminder/expiry jobs remain; only backups need operational scheduling | Requests leave old applications/outbox unchanged | No booking scheduler required |
| Desktop/mobile QA | Not tested | Access to the browser preview or manual review | Browser automation was denied by security policy; current pages have server-rendered checks but no current screenshots | Check home, host, forms, confirmation and admin at desktop and narrow-phone sizes, including keyboard use | Yes before public launch |

## 5. Brand and programme readiness

| Item | Current status | You supply/decide | Connect/change | Verify | Blocks? |
|---|---|---|---|---|---|
| Brand | Needs decision | Confirm Open Estia name, domain/social availability and relevant trademark review | Update branding if needed; original local vector/PNG kit exists | Name and assets consistent | Yes |
| Real hosts | Needs decision | Approved real host details and commitments | Replace labelled samples in the operator editor; confirm dates, sleeping setup, accessibility and each free benefit | Host reviews the exact published page | Yes |
| Photographs | Needs decision | Rights for Philoxenia/YC/Mistral reference images or replacements | Obtain permission covering the use or replace in the local code/editor before public use | Written permission / licence and accurate credits | Yes for these images |
| Privacy and terms | Needs decision | Operator identity, contact, retention/deletion policy and final programme rules | Review current draft, add final details and record real consent appropriately | Form disclosures match actual handling | Yes |
| Editorial upkeep | Ready locally | Who selects stories and how often | Edit dated summaries, sources and photos in Journal; no automated feed | Links and dates are accurate; old stories marked clearly | Operational decision |
| Programme support | Needs decision | Contact channel and procedures for issues, cancellations and emergencies | Supply public support email and agree procedures offline | Participants know whom to contact and how | Yes |

## Connection order

1. **First action: open /admin and replace or pause the sample host profiles.** Confirm the real offers and collect approved photos.
2. Confirm the name, public support contact, programme/privacy rules, image permissions and the real operator credentials.
3. Choose a Python hosting target with persistent storage; configure domain, HTTPS, production server, trusted hosts and secure sessions.
4. Transfer selected records and files, configure backups/monitoring and verify a clean restore. Confirm your personal email/WhatsApp follow-up process.
5. Run desktop/mobile and permission checks on the deployment, submit both forms, review the inbox and deliberately complete a manual follow-up before opening publicly.

## Environment variables

Supported locally: OPEN_ESTIA_DATA_DIR, OPEN_ESTIA_BASE_URL, OPEN_ESTIA_PORT, OPEN_ESTIA_SESSION_HOURS, OPEN_ESTIA_COOKIE_SECURE, OPEN_ESTIA_SECRET_KEY. The old OPEN_ESTIA_EMAIL_MODE and OPEN_ESTIA_OFFER_HOURS settings are unused and removed from .env.example. No secret values are included in this report.
