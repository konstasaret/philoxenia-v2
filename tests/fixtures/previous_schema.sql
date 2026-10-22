
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, name TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','host','guest')), verified INTEGER NOT NULL DEFAULT 0,
 adult INTEGER NOT NULL DEFAULT 1, eligibility TEXT NOT NULL DEFAULT 'pending' CHECK(eligibility IN ('pending','approved','declined')),
 background TEXT NOT NULL DEFAULT '', project TEXT NOT NULL DEFAULT '', links TEXT NOT NULL DEFAULT '',
 auth_version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS hosts(
 id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL REFERENCES users(id), background TEXT NOT NULL,
 interests TEXT NOT NULL, motivation TEXT NOT NULL, builders TEXT NOT NULL,
 review_label TEXT NOT NULL DEFAULT 'Not yet reviewed', sample INTEGER NOT NULL DEFAULT 0,
 headline TEXT NOT NULL DEFAULT '', portrait TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS host_submissions(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, city TEXT NOT NULL, background TEXT NOT NULL,
 proposal TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS homes(
 id INTEGER PRIMARY KEY, host_id INTEGER NOT NULL REFERENCES hosts(id), title TEXT NOT NULL, city TEXT NOT NULL,
 area TEXT NOT NULL, address TEXT NOT NULL, sleeping TEXT NOT NULL, shared TEXT NOT NULL,
 accessibility TEXT NOT NULL, rules TEXT NOT NULL, commitments TEXT NOT NULL,
 nightly_cost INTEGER NOT NULL DEFAULT 0 CHECK(nightly_cost=0), currency TEXT NOT NULL DEFAULT '', extra_costs TEXT NOT NULL DEFAULT '',
 benefits TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published','paused')),
 image TEXT NOT NULL DEFAULT 'home-lisbon.svg', sample INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS periods(
 id INTEGER PRIMARY KEY, home_id INTEGER NOT NULL REFERENCES homes(id), start TEXT NOT NULL, end TEXT NOT NULL,
 capacity INTEGER NOT NULL CHECK(capacity>0 AND capacity<=20), active INTEGER NOT NULL DEFAULT 1, CHECK(start<end));
CREATE TABLE IF NOT EXISTS applications(
 id INTEGER PRIMARY KEY, guest_id INTEGER NOT NULL REFERENCES users(id), period_id INTEGER NOT NULL REFERENCES periods(id),
 start TEXT NOT NULL, end TEXT NOT NULL, background TEXT NOT NULL, project TEXT NOT NULL, links TEXT NOT NULL,
 outcome TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'submitted',
 interview_notes TEXT NOT NULL DEFAULT '', host_summary TEXT NOT NULL DEFAULT '', interview_link TEXT NOT NULL DEFAULT '',
 request_text TEXT NOT NULL DEFAULT '', answer TEXT NOT NULL DEFAULT '', host_reason TEXT NOT NULL DEFAULT '',
 terms TEXT NOT NULL DEFAULT '{}', deadline TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(guest_id,period_id));
CREATE TABLE IF NOT EXISTS tokens(
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), digest TEXT UNIQUE NOT NULL, purpose TEXT NOT NULL,
 expires_at TEXT NOT NULL, used INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS templates(name TEXT PRIMARY KEY, subject TEXT NOT NULL, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(
 id INTEGER PRIMARY KEY, recipient TEXT NOT NULL, template TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
 link TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', attempts INTEGER NOT NULL DEFAULT 0,
 event_key TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL, delivered_at TEXT);
CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), application_id INTEGER REFERENCES applications(id),
 kind TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reports(
 id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), contact TEXT NOT NULL, detail TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open', resolution TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS media(
 id TEXT PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id), home_id INTEGER REFERENCES homes(id),
 filename TEXT NOT NULL, original_name TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rate_limits(key TEXT PRIMARY KEY, count INTEGER NOT NULL, until TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS apps_period_status ON applications(period_id,status);
CREATE INDEX IF NOT EXISTS apps_guest ON applications(guest_id);
