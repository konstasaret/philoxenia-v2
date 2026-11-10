# The Godfather

**A place to stay. People to know.**

A completely legal global network of Greeks and builders who share knowledge, resources, introductions, and a place to start. The ambition: a huge, successful family that helps the next generation grow, then asks them to reach back and help someone else.

**Godfathers** are experienced people who provide free accommodation (an air mattress, couch or room), guidance and local support; meals, gym access and introductions may be available as additional benefits. **Associates** are newer builders looking to learn, work on their ambitions, and contribute. Both roles are open to all genders. Participation and offered support are free; the pilot is for adults 18+.

Philoxenia by Hustle Hours is credited as the spark. This is an independent initiative, not a claim of official affiliation. The worldwide city network is a vision; sample profiles are not confirmed members.

## Start locally

Use Python 3.9+; a maintained Python version is recommended for new installations.

```sh
git clone https://github.com/konstasaret/philoxenia-v2.git
cd philoxenia-v2
./start.sh
```

The first start installs Python dependencies in `.venv`. Then open:

- Website: http://127.0.0.1:5073/
- Associate form: http://127.0.0.1:5073/join
- Godfather form: http://127.0.0.1:5073/become-a-godfather
- Private operator dashboard: http://127.0.0.1:5073/admin

**Fresh-demo operator:** `admin@greekmafia.local` / `GreekMafiaDemo!2026`. These intentionally public credentials are for local use only. An existing installation retains its previous credentials and all records; the rebrand does not change its login.

The server binds to localhost. A GitHub source upload does not deploy the website.

## What is included

1. A new identity, original connected-network mark, English display titles, Greek body copy, and an ink/ivory/olive/coral palette.
2. A community manifesto, the personal impact of finding support, respectful Philoxenia credit, an aspirational global network, the Godfather role, and a clear give-back code.
3. Animated typography, a rotating seal, a locally rendered rotating Earth with animated connections and five city/Godfather spotlights (tech in San Francisco, AI in London, VC in Athens, founders in Amsterdam and academia in Stockholm), and entrance reveals. A visible motion control, reduced-motion support, and readable no-JavaScript/error fallbacks are included.
4. Two private inquiry forms requiring name, email, an international phone number and a one-minute written personal pitch (about 120–150 words) covering identity, motivation, aspirations and goals. Inquiries are followed up personally by email or WhatsApp. No member accounts, automated matching, payments, automatic messages or bookings.
5. An operator inbox, private notes/status, editable Godfather profiles with hosting arrangements, editable introductory copy, backup/restore, and preserved historical records.

Every Godfather hosts an Associate on an air mattress, couch or in a room. A sleeping arrangement is required before publishing a profile; incomplete drafts can be saved. Meals, gym access, introductions and other additional benefits remain individually marked included, conditional or unavailable.

## Source and data

Homepage: `templates/v2/index.html`. Public design: `static/mafia.css`. Motion controller: `static/mafia.js`. Shared forms/operator styles: `static/editorial.css`. Default copy: `intake_seed.py`. Current vector assets: `static/brand/greek-mafia-mark.svg` and `greek-mafia-wordmark.svg`.

Private records, uploads, backups and signing secrets stay under `.data/`, excluded from Git along with `.env`. Normal runtime needs no remote images, fonts, API keys or cloud services.

For continuity, the existing `OPEN_ESTIA_*` environment names, `open-estia.sqlite3` filename, and stored `guest`/`host` role keys are retained internally. They map to Associate/Godfather in the interface. Old `/apply`, `/become-a-host`, `/explore` and `/homes/<id>` URLs still work. Public navigation uses the new role names and routes.

Untouched previous starter copy upgrades once. Operator-written copy and contact email are preserved. Use **Website** in the private dashboard to edit your own story.

## Checks and operation

```sh
.venv/bin/python -m pytest -q
node --test tests/motion.test.cjs tests/globe.test.cjs
.venv/bin/python manage.py backup
.venv/bin/python manage.py operator --email your-address@example.com
```

Node is only needed for the optional motion-controller unit tests, not for running the site. The operator command asks for a password securely. Stop the server before resetting or restoring data:

```sh
.venv/bin/python manage.py reset --confirm RESET-SAMPLE-DATA
.venv/bin/python manage.py restore --backup /absolute/path/to/backup --confirm RESTORE-BACKUP
```

Both commands first create a recovery backup. Reset replaces active data with samples; restore preserves earlier supported databases.

## Verification and launch

See [test results](docs/TEST-RESULTS.md), [operator instructions](docs/OPERATOR-GUIDE.md), [design](docs/BRAND.md), [architecture](docs/WORKFLOWS.md), [photo credits](docs/PHOTO-SOURCES.md), and [launch readiness](docs/READINESS.md).

Functional, motion-controller and server-rendered checks are distinct from visual browser QA. On October 22, 2026, the owner confirmed that the homepage layout, animations, motion button and both forms display correctly at desktop and narrow-phone widths. This was manual verification; automated browser access was restricted and no screenshots were produced. Public launch also needs hosting/HTTPS, production credentials, real member commitments, final privacy/support details, and appropriate image permissions. No public site has been deployed.

Builder Stories has been removed from the public site. The former `/journal` URL redirects to the homepage. Existing story records and private management routes are retained.

Godfathers appear in one compact directory at `/godfathers`, with a city filter and brief hosting/support summaries; external profile links are not shown. Former individual `/godfathers/<id>` and `/homes/<id>` URLs redirect to the matching row for published entries. Draft/paused entries remain hidden.

The November 10, 2026 homepage revision trims repeated copy, brings The Code forward as chapter 04, and removes the process banner. The latest source passed 63 Python tests, 11 JavaScript tests and local Chrome responsive checks at 1440, 768, 390 and 320 px; details are in `docs/TEST-RESULTS.md`.
