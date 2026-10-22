import argparse
import getpass
import secrets
import shutil
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
from app import create_app
from store import db, execute, init_db, one
from intake_seed import seed
from operations import backup

parser=argparse.ArgumentParser(description='Open Estia local operator tools')
parser.add_argument('command',choices=['init','backup','restore','reset','operator'])
parser.add_argument('--confirm',default='')
parser.add_argument('--backup',help='Backup directory to restore')
parser.add_argument('--email',help='Operator email for the operator command')
args=parser.parse_args()
app=create_app()
with app.app_context():
    data=Path(app.config['DATA_DIR'])
    if args.command=='init':
        print('Open Estia ready. Existing data preserved; public forms and operator dashboard enabled.')
    elif args.command=='backup':
        print('Backup saved:',backup(db(),data))
    elif args.command=='operator':
        import re
        if not args.email or not re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',args.email): parser.error('Supply --email with a valid operator email.')
        password=getpass.getpass('New operator password (12–128 characters): ')
        if not 12<=len(password)<=128: parser.error('Password must be 12–128 characters.')
        if password!=getpass.getpass('Repeat password: '): parser.error('Passwords did not match.')
        operator=one('SELECT id FROM operators ORDER BY id LIMIT 1')
        execute('UPDATE operators SET email=?,password=?,auth_version=auth_version+1 WHERE id=?',(args.email.lower(),generate_password_hash(password,method='pbkdf2:sha256:1000000'),operator['id']))
        print('Operator credentials updated. Existing operator sessions are invalidated.')
    elif args.command=='reset':
        if args.confirm!='RESET-SAMPLE-DATA': parser.error('Stop the server. Supply --confirm RESET-SAMPLE-DATA. A backup is made first.')
        print('Backup saved:',backup(db(),data))
        conn=db();conn.execute('PRAGMA foreign_keys=OFF')
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
            conn.execute('DROP TABLE "'+row['name'].replace('"','""')+'"')
        conn.execute('PRAGMA foreign_keys=ON')
        shutil.rmtree(data/'uploads');(data/'uploads').mkdir(mode=0o700)
        init_db();seed()
        (data/'secret.key').write_text(secrets.token_hex(48));(data/'secret.key').chmod(0o600)
        print('Reset complete. Restart the server. Rotate any environment-provided secret too.')
    elif args.command=='restore':
        if args.confirm!='RESTORE-BACKUP' or not args.backup: parser.error('Stop the server. Supply --backup PATH --confirm RESTORE-BACKUP.')
        source=Path(args.backup).resolve()
        if not (source/'open-estia.sqlite3').is_file() or not (source/'uploads').is_dir(): parser.error('Backup must contain the database and uploads directory.')
        check=sqlite3.connect(str(source/'open-estia.sqlite3'))
        if check.execute('PRAGMA integrity_check').fetchone()[0]!='ok': parser.error('Backup database integrity check failed.')
        tables={r[0] for r in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'operators','users'}.intersection(tables): parser.error('This is not an Open Estia backup.')
        print('Current data backup:',backup(db(),data))
        check.backup(db());check.close()
        shutil.rmtree(data/'uploads');shutil.copytree(source/'uploads',data/'uploads')
        (data/'secret.key').write_text(secrets.token_hex(48));(data/'secret.key').chmod(0o600)
        print('Restored. Restart the server; old databases migrate automatically. Rotate any environment-provided secret too.')
