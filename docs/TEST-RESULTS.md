# Verification — October 21, 2026 (Pacific)

## Current result

**50 functional tests passed in 19.78 seconds.** Command: `.venv/bin/python -m pytest -q`. Output: `test-output.txt`.

The current homepage is the community-and-invitation design: **A bigger world. A familiar face.** It retains the simplified forms and operator workflow.

## What was checked

1. Public pages and local assets; anonymous guest and host intake; validation preserving input; consent; saved records surviving restart; duplicate and simultaneous submission handling.
2. Private operator access; rejection of participant sessions; removed booking/account routes; login and session invalidation; CSRF including malformed tokens; rate limiting; escaped user content.
3. Private notes and manual status; email/WhatsApp links; editing, publishing and pausing hosts and stories; saved homepage copy. Long benefit descriptions remain editable.
4. Image validation, metadata removal, access restrictions, paused-host applications, source URL validation, and repeatable seeding without overwriting saved edits.
5. Legacy import without modifying original tables; no background booking/email jobs; backup, reset and restore against temporary test data.

No messages were sent. Functional tests use temporary data and do not modify local participant records.

## Structure and accessibility checks

32 pages were rendered using an isolated copy of the local database. Every checked page returned HTTP 200, had one main heading, unique IDs, labelled fields, no nested forms, valid internal links and resolvable local image/styles. The homepage story order and new stylesheet were checked. All seven checked text/background pairs exceeded 4.5:1 contrast.

Results: `movement-render-checks.json`. The report contains no inquiry content or private contact details.

The public styling includes desktop, tablet and phone breakpoints, keyboard focus indicators, 44px-or-larger primary navigation/action targets, and 16px mobile form inputs. Source inspection and rendered HTML are not proof of browser appearance.

## Visual verification limit

The current desktop/mobile layout and actual browser interactions have **not** been visually verified. Preview access was previously denied by browser security policy, including retry or alternate browser paths. No workaround or screenshot claim is made.

Before public launch, inspect the homepage, host directory/profile, journal, both forms, validation/confirmation and operator screens at desktop and phone widths, including keyboard focus and horizontal overflow.

## Source delivery

Git excludes the local database, backups, private uploads, signing secret, environment files, virtual environment, caches and historical private-dataset audits. The repository provides the app, local reference/brand assets, sample content, documentation and tests. A source upload is not a hosted deployment.
