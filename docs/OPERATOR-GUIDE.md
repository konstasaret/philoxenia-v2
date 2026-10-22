# Open Estia operator guide

## Your everyday flow

1. Open http://127.0.0.1:5073/admin and sign in with `admin@openestia.local` / `OpenEstiaDemo!2026`.
2. Open a guest or host inquiry. Read their message, dates, links and contact details.
3. Use **Open email** or **Open WhatsApp** to continue personally. The site does not send the message.
4. Save private notes and choose **New**, **Contacted**, **Arranged** or **Closed**. These are tracking labels, not bookings or notifications.
5. Manage published hosts and stories when your available places or editorial selections change.

## Guests and prospective hosts

Guests use `/apply`; hosts use `/become-a-host`. Neither creates an account. A host profile's application link preselects that host. Dates are free text, so you can arrange them without a booking calendar. People can leave the host choice open.

Both forms collect name, email, an optional WhatsApp number with country code, a message, optional links, and 18+/contact consent. The host form also asks for the city. The guest form offers optional city and date preferences. Submitted information is private.

The confirmation page acknowledges saving; it does not claim an email was sent. Repeating the same submission does not create a duplicate. Validation errors keep entered text.

## Edit what is on the site

**Hosts** combines the person and their accommodation in one editor. Add the name, English specialty, city, Greek introduction, sleeping arrangement, availability, house details and benefits. All offered benefits are free. Mark meals, gym access, workspace, support and introductions as included, conditional or unavailable; explain any conditions.

The exact address, host email, phone and notes are operator-only. Uncheck the fictional-sample label only for a real profile. Save as **Published** to show it, **Paused** to hide it, or **Draft** while preparing it. Lower display-order numbers appear first. A submitted host form never publishes itself.

**Journal** controls source-linked stories, English titles, Greek summaries, publication dates and photos. Use the original date, especially for older stories. There is no automatic news feed. The first three published stories appear on the homepage; all appear in the journal.

Photo uploads support JPEG, PNG and WebP up to 8 MB and 20 megapixels. Add a descriptive alternative text and credit. Files are re-encoded locally with metadata removed. Draft and paused uploads are inaccessible publicly unless the same image is attached to another published entry.

**Website** controls introductory copy and your public support email. Fixed headings preserve the English / Greek design.

## Previous records

Earlier applications, host submissions and reports are imported into the inbox. Each retains its original record under a disclosure. Historical notes remain private. Earlier accounts, stays, local email history and decisions can be inspected under **Previous records**.

Old tables are not modified by the simplified app. Old guest/host passwords cannot sign in. There are no outstanding-offer timers, capacity calculations or automatic emails. An imported “Arranged” label simply reflects the previous confirmed status.

## Keep a backup

```sh
.venv/bin/python manage.py backup
```

The command snapshots the database and copies uploads to `.data/backups/backup-TIMESTAMP/`. Backups contain private records; keep them private.

Stop the server before restore:

```sh
.venv/bin/python manage.py restore --backup /absolute/path/to/backup --confirm RESTORE-BACKUP
./start.sh
```

The existing data is backed up first. A restored old database is imported automatically at startup. Reset is optional and destructive to the active dataset, with a recovery backup:

```sh
.venv/bin/python manage.py reset --confirm RESET-SAMPLE-DATA
```

Reset and restore rotate the local signing-key file. If you set `OPEN_ESTIA_SECRET_KEY`, rotate that value yourself and restart. A forgotten operator password is reset locally with `manage.py operator --email your-email`; no email provider is required.
