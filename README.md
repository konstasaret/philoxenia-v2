# Open Estia

**Find your people and build**

Greek roots. Open doors. Everywhere. Open Estia is an early hospitality project for a global Greek community and the wider community of builders: people sharing a place to stay, a little time, and what they have learned.

The website tells that story through English headlines and Greek body copy. Philoxenia by Hustle Hours is credited as the inspiration. The worldwide network is a vision, not a claim of confirmed hosts in every city. All seeded host profiles are explicitly fictional examples.

## Run locally

Requires Python 3.9+ (use a maintained Python version for new installations).

```sh
git clone https://github.com/konstasaret/philoxenia-v2.git
cd philoxenia-v2
./start.sh
```

The first start creates a virtual environment and installs dependencies. Then open:

- Website: http://127.0.0.1:5073/
- Private operator dashboard: http://127.0.0.1:5073/admin
- Local demo login: `admin@openestia.local` / `OpenEstiaDemo!2026`

The demo password is intentionally public and for local use only. The server binds to localhost. Uploading this source repository does not deploy the website.

## The experience

1. **The story:** Greek community, Philoxenia's spark, bigger ambitions, and the vision of builders opening their homes around the world.
2. **The invitation:** meet host examples, understand the sleeping arrangement and the free offer, then fill in a short form. No guest or host accounts.
3. **The practical details:** personal follow-up, agreed dates and expectations, conditional extras, and clear responsibilities.
4. **The people behind it:** an honest note about starting small. Sourced builder stories sit further down the page as reading, not as proof of partnerships.
5. **The operator:** private inquiries, notes and manual status; create/edit/publish/pause hosts and journal stories; edit introductory copy. Email and WhatsApp buttons only open the relevant app.

## Your data

The database, private uploads, backups and a randomly generated signing secret are stored under `.data/`. This folder and `.env` are ignored by Git and are not included in this repository. Normal use needs no cloud account, API key, remote font, remote image, or automated messaging service.

A fresh checkout creates three sample hosts, three sourced stories, one demo operator and an empty inbox. Existing local databases are preserved. Earlier Open Estia records are imported without deleting their original tables; only the operator can read the historical archive.

The public homepage is `templates/v2/index.html`. Its public styles are in `static/movement.css`; shared form and operator styles are in `static/editorial.css`. Initial copy is in `intake_seed.py`. Editing defaults does not overwrite an existing operator's saved copy; use **Website** in the dashboard for that.

## Checks and operation

```sh
.venv/bin/python -m pytest -q
.venv/bin/python manage.py backup
.venv/bin/python manage.py operator --email your-address@example.com
```

The operator command prompts for a new password and invalidates older sessions. Stop the server before reset or restore. Both preserve a recovery backup:

```sh
.venv/bin/python manage.py reset --confirm RESET-SAMPLE-DATA
.venv/bin/python manage.py restore --backup /absolute/path/to/backup --confirm RESTORE-BACKUP
```

## What this repository is ready for

Local demonstration and further development. There is no public deployment, automated booking, payments, messaging, matching, or participant dashboard. Hosting, HTTPS, production credentials, real host commitments and final programme/privacy details still need to be configured before a public launch.

Functional and server-rendered checks are documented in [test results](docs/TEST-RESULTS.md). The current desktop/mobile layout has not been visually verified in a browser because preview access was restricted in the development session. Reference photos remain attributed to their sources; public reuse rights have not been verified.

Read the [operator guide](docs/OPERATOR-GUIDE.md), [launch readiness](docs/READINESS.md), [architecture](docs/WORKFLOWS.md), [design story](docs/BRAND.md), and [photo credits](docs/PHOTO-SOURCES.md).
