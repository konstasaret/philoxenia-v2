"""Local backup helpers shared by migration and the operator command line."""
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def backup(connection, data, label='backup'):
    data=Path(data)
    folder=data/'backups'/(label+'-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    folder.mkdir(parents=True,mode=0o700)
    target=sqlite3.connect(str(folder/'open-estia.sqlite3'))
    try: connection.backup(target)
    finally: target.close()
    (folder/'open-estia.sqlite3').chmod(0o600)
    shutil.copytree(data/'uploads',folder/'uploads')
    return folder
