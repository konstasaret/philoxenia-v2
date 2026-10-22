"""Small operator-managed directory and inquiry inbox. Legacy tables are never dropped."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from flask import current_app, g


def stamp():
    return datetime.now(timezone.utc).isoformat()


def db():
    if 'store' not in g:
        g.store = sqlite3.connect(current_app.config['DATABASE'], timeout=15, isolation_level=None)
        g.store.row_factory = sqlite3.Row
        g.store.execute('PRAGMA foreign_keys=ON')
    return g.store


def one(sql, args=()): return db().execute(sql, args).fetchone()
def rows(sql, args=()): return db().execute(sql, args).fetchall()
def execute(sql, args=()): return db().execute(sql, args)


def close_db(_=None):
    conn = g.pop('store', None)
    if conn is not None: conn.close()


@contextmanager
def atomic():
    conn = db()
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


SCHEMA = '''
CREATE TABLE IF NOT EXISTS intake_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS operators(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password TEXT NOT NULL, auth_version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS listings(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, headline TEXT NOT NULL, city TEXT NOT NULL, area TEXT NOT NULL DEFAULT '',
 background TEXT NOT NULL, sleeping TEXT NOT NULL, shared TEXT NOT NULL DEFAULT '', accessibility TEXT NOT NULL DEFAULT '',
 rules TEXT NOT NULL DEFAULT '', commitments TEXT NOT NULL DEFAULT '', benefits TEXT NOT NULL DEFAULT '{}',
 availability TEXT NOT NULL DEFAULT '', status TEXT NOT NULL CHECK(status IN ('draft','published','paused')),
 sample INTEGER NOT NULL DEFAULT 0, position INTEGER NOT NULL DEFAULT 0, image TEXT NOT NULL DEFAULT '',
 image_alt TEXT NOT NULL DEFAULT '', image_credit TEXT NOT NULL DEFAULT '',
 contact_email TEXT NOT NULL DEFAULT '', contact_phone TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '',
 private_notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS inquiries(
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('guest','host','support')), name TEXT NOT NULL,
 email TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '', listing_id INTEGER REFERENCES listings(id),
 listing_label TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '', dates TEXT NOT NULL DEFAULT '',
 message TEXT NOT NULL, links TEXT NOT NULL DEFAULT '', adult INTEGER NOT NULL DEFAULT 1,
 consent_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','contacted','arranged','closed')),
 notes TEXT NOT NULL DEFAULT '', submission_key TEXT UNIQUE NOT NULL, legacy_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS stories(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, summary TEXT NOT NULL, city TEXT NOT NULL,
 category TEXT NOT NULL DEFAULT 'Dispatch', published_on TEXT NOT NULL, source_name TEXT NOT NULL, source_url TEXT NOT NULL,
 image TEXT NOT NULL DEFAULT '', image_alt TEXT NOT NULL DEFAULT '', image_credit TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL CHECK(status IN ('draft','published','paused')), position INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS site_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS intake_limits(key TEXT PRIMARY KEY, count INTEGER NOT NULL, until TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS inquiry_status_date ON inquiries(status,created_at);
'''


def init_db():
    existing={r['name'] for r in rows("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'users' in existing and ('intake_migrations' not in existing or not one('SELECT 1 FROM intake_migrations WHERE version=1')):
        from operations import backup
        backup(db(),current_app.config['DATA_DIR'],'before-intake-migration')
    db().executescript(SCHEMA)
    if one('SELECT 1 FROM intake_migrations WHERE version=1'): return
    tables = {r['name'] for r in rows("SELECT name FROM sqlite_master WHERE type='table'")}
    with atomic():
        if 'users' in tables:
            for u in rows("SELECT * FROM users WHERE role='admin'"):
                execute('INSERT OR IGNORE INTO operators(id,email,name,password,auth_version) VALUES(?,?,?,?,?)',
                        (u['id'],u['email'],u['name'],u['password'],u['auth_version']))
        if 'homes' in tables:
            for h in rows('SELECT h.*,u.name,u.email,hp.headline,hp.background FROM homes h JOIN hosts hp ON hp.id=h.host_id JOIN users u ON u.id=hp.user_id'):
                periods = rows('SELECT start,end,capacity FROM periods WHERE home_id=? AND active=1 ORDER BY start', (h['id'],))
                availability = '\n'.join('{} → {} · {} θέση/θέσεις'.format(p['start'],p['end'],p['capacity']) for p in periods)
                fields = dict(id=h['id'],name=h['name'],headline=h['headline'],city=h['city'],area=h['area'],
                              background=h['background'],sleeping=h['sleeping'],shared=h['shared'],accessibility=h['accessibility'],
                              rules=h['rules'],commitments=h['commitments'],benefits=h['benefits'],availability=availability,
                              status=h['status'],sample=h['sample'],position=0 if h['email']=='host.sf@openestia.local' else h['id'],
                              contact_email=h['email'],address=h['address'],updated_at=stamp())
                insert('listings', fields)
        if 'applications' in tables:
            for a in rows('SELECT a.*,u.name,u.email,p.home_id FROM applications a JOIN users u ON u.id=a.guest_id JOIN periods p ON p.id=a.period_id'):
                listing=one('SELECT * FROM listings WHERE id=?',(a['home_id'],))
                status={'confirmed':'arranged','completed':'closed','declined':'closed','cancelled':'closed','withdrawn':'closed','expired':'closed','submitted':'new'}.get(a['status'],'contacted')
                insert('inquiries',dict(kind='guest',name=a['name'],email=a['email'],listing_id=a['home_id'],
                    listing_label=listing['name']+' · '+listing['city'],dates=a['start']+' → '+a['end'],
                    message='\n\n'.join(v for v in [a['background'],a['project'],a['outcome'],a['reason']] if v),links=a['links'],
                    consent_at='',status=status,notes=a['interview_notes'],submission_key='legacy-application-'+str(a['id']),
                    legacy_json=json.dumps(dict(a),ensure_ascii=False),created_at=a['created_at'],updated_at=a['updated_at']))
        if 'host_submissions' in tables:
            for h in rows('SELECT * FROM host_submissions'):
                insert('inquiries',dict(kind='host',name=h['name'],email=h['email'],city=h['city'],message=h['background']+'\n\n'+h['proposal'],
                    consent_at='',status='new' if h['status']=='pending' else 'contacted',submission_key='legacy-host-'+str(h['id']),
                    legacy_json=json.dumps(dict(h),ensure_ascii=False),created_at=h['created_at'],updated_at=h['created_at']))
        if 'reports' in tables:
            for r in rows('SELECT * FROM reports'):
                u=one('SELECT name,email FROM users WHERE id=?',(r['user_id'],))
                insert('inquiries',dict(kind='support',name=u['name'] if u else 'Previous report',email=u['email'] if u else '',message=r['detail'],
                    consent_at='',status='new' if r['status']=='open' else 'closed',notes=r['resolution'],submission_key='legacy-report-'+str(r['id']),
                    legacy_json=json.dumps(dict(r),ensure_ascii=False),created_at=r['created_at'],updated_at=r['created_at']))
        execute('INSERT INTO intake_migrations VALUES(1,?)',(stamp(),))


def insert(table, values):
    # Table and field names come only from application-owned dictionaries.
    names=','.join(values)
    marks=','.join('?' for _ in values)
    return execute('INSERT INTO '+table+' ('+names+') VALUES('+marks+')',tuple(values.values())).lastrowid


def update(table, record_id, values):
    execute('UPDATE '+table+' SET '+','.join(k+'=?' for k in values)+' WHERE id=?',tuple(values.values())+(record_id,))


def settings(): return {r['key']:r['value'] for r in rows('SELECT * FROM site_settings')}
