# Verification — October 22, 2026

## Current results

**53 Python checks passed in 21.49 seconds.** Run `.venv/bin/python -m pytest -q`; output is in `test-output.txt`.

**6 motion-controller checks passed.** Run `node --test tests/motion.test.cjs`. These execute the local controller with mocked DOM interfaces; they are not browser visual tests.

The current identity is **Greek Mafia — Big ambition. Bigger family.**

## Functional coverage

1. Canonical Associate/Godfather forms, old-route compatibility, private role-labelled intake, validation, explicit adult/contact consent, duplicate handling, concurrency, and persistence across restart.
2. Operator authentication, retained legacy credentials, session invalidation, rejected participant sessions, CSRF, malformed input, request limits and escaped content.
3. Private notes/status, safe manual email/WhatsApp links, editing/publishing/pausing profiles and stories, and Godfathers offering mentoring without accommodation. Blank sleeping text explicitly means no stay.
4. Image validation/re-encoding, hidden draft images, paused-profile submissions, valid source URLs and repeatable seeding. The brand upgrade replaces untouched defaults while preserving custom copy, records and contact email.
5. Legacy import preserving original tables and details, local backups, reset and restore. No automatic matching, booking, messaging or expiry processes are introduced.

Tests use temporary records. No messages are sent and no live inquiry data is modified.

## Motion coverage

Pause/resume and state labels; reduced-motion settings; no IntersectionObserver fallback; observer-initialization failure; one-time entrance reveal; keyboard-focus visibility; preference changes; printing. CSS keeps content visible before JavaScript enhancement and disables animation for reduced-motion preferences.

## Rendered-page and contrast checks

38 public and operator pages rendered successfully against an isolated database copy. Checks verified one main heading per page, unique IDs, labelled fields, no nested forms, resolvable internal links and local assets, and no old public brand. The homepage's family → story → world → Godfather → give-back → two-entry-point order is present.

All seven sampled text/background pairs exceed 4.5:1. Results are in `mafia-render-checks.json`. These are source and server-rendered checks, not proof of visual alignment, clipping or animation appearance.

## Remaining visual review

Desktop/mobile browser review is **pending**. Browser security previously denied localhost automation and prohibited retry/alternate browser paths. No workaround was used.

Inspect the homepage at desktop and narrow-phone widths: hero lettering, seal/photo overlap, ticker, story, network, role cards, focus and the Pause motion control. Then inspect both forms, errors, confirmation, a Godfather profile without accommodation and the private inbox. Motion-controller unit checks do not replace this review.

## Source and data boundary

Local records, backups, uploads, secrets and environment files stay excluded from Git. A row-by-row comparison with the pre-rebrand backup confirmed that all 21 tables other than website settings were unchanged. Existing credentials remain unchanged. The source repository contains only app code, public assets, clearly labelled examples, tests and documentation. Source delivery does not mean public hosting.
