import io
import json
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from PIL import Image
from app import create_app
from intake_seed import DEMO_PASSWORD
from store import execute, one, rows, settings

@pytest.fixture
def site(tmp_path):
    return create_app({'TESTING':True,'DATA_DIR':str(tmp_path),'SECRET_KEY':'intake-test-key'})

@pytest.fixture
def visitor(site): return site.test_client()

def submit(client,path,data):
    with client.session_transaction() as s: csrf=s['csrf']
    return client.post(path,data=dict(data,csrf=csrf))

def form_data(client,path='/apply',**overrides):
    assert client.get(path).status_code==200
    with client.session_transaction() as s: key=s['form_keys'][-1]
    data=dict(name='Alex Builder',email='alex@example.test',phone='+30 691 234 5678',message='I am building a working prototype and want to meet other builders.',adult='1',consent='1',submission_key=key)
    data.update(overrides)
    return data

def operator(site):
    client=site.test_client(); client.get('/admin/login')
    response=submit(client,'/admin/login',dict(email='admin@openestia.local',password=DEMO_PASSWORD))
    assert response.status_code==302 and response.location=='/admin'
    return client

def listing_payload():
    return dict(name='Test Host',headline='Embedded engineer',city='Athens',area='Centre',background='A real edited profile.',sleeping='One couch for one adult.',availability='June, by arrangement.',status='draft',position='5',address='PRIVATE EXACT ADDRESS',private_notes='PRIVATE OPERATOR NOTE')

def photo():
    output=io.BytesIO(); Image.new('RGB',(64,40),'green').save(output,format='PNG'); output.seek(0)
    return output

@pytest.mark.parametrize('path',['/','/explore','/journal','/homes/1','/apply','/become-a-host','/program','/admin/login'])
def test_public_routes_and_local_assets(visitor,path):
    response=visitor.get(path); assert response.status_code==200
    html=response.get_data(as_text=True)
    if path!='/admin/login':
        assert '/register' not in html and 'My dashboard' not in html and 'Sign in' not in html
    for source in re.findall(r'(?:src|href)="([^"]+)"',html):
        if source.startswith('/static/'):
            assert visitor.get(source).status_code==200,source
        assert not source.startswith(('https://fonts.','https://images.'))

def test_guest_form_no_account_persists_across_restart(site,visitor):
    data=form_data(visitor,listing_id='3',dates='Two weeks in June',city='SF',links='https://example.test/project')
    response=submit(visitor,'/apply',data)
    assert response.location=='/thanks'
    assert 'Λάβαμε την αίτησή σου.' in visitor.get(response.location).get_data(as_text=True)
    with site.app_context():
        item=one('SELECT * FROM inquiries')
        assert item['name']=='Alex Builder' and item['status']=='new' and item['phone']=='+306912345678'
        assert item['consent_at'] and item['listing_label'].startswith('Chris & Theo')
        assert one('SELECT count(*) n FROM operators')['n']==1
        assert not one("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'")
    restarted=create_app(dict(TESTING=True,DATA_DIR=site.config['DATA_DIR'],SECRET_KEY='intake-test-key'))
    with restarted.app_context(): assert one('SELECT count(*) n FROM inquiries')['n']==1

def test_host_form_is_private_and_does_not_publish(site,visitor):
    data=form_data(visitor,'/become-a-host',city='Copenhagen')
    assert submit(visitor,'/become-a-host',data).status_code==302
    with site.app_context():
        assert one('SELECT kind FROM inquiries')['kind']=='host'
        assert one('SELECT count(*) n FROM listings')['n']==3
    assert 'Copenhagen' not in visitor.get('/explore').get_data(as_text=True)
    inbox=operator(site).get('/admin?kind=host').get_data(as_text=True)
    assert 'Alex Builder' in inbox and 'Copenhagen' in inbox

def test_validation_preserves_input_and_no_partial_record(site,visitor):
    data=form_data(visitor,email='bad',phone='12345',adult='',consent='',links='javascript:alert(1)')
    response=submit(visitor,'/apply',data)
    assert response.status_code==422
    html=response.get_data(as_text=True)
    assert 'Alex Builder' in html and 'working prototype' in html and 'aria-invalid="true"' in html
    with site.app_context(): assert not one('SELECT id FROM inquiries')
    data.update(email='alex@example.test',phone='',adult='1',consent='1',links='')
    assert submit(visitor,'/apply',data).status_code==302

def test_duplicate_submission_is_idempotent(site,visitor):
    data=form_data(visitor)
    assert submit(visitor,'/apply',data).status_code==302
    assert submit(visitor,'/apply',data).status_code==302
    with site.app_context(): assert one('SELECT count(*) n FROM inquiries')['n']==1

def test_concurrent_duplicate_submission(site,visitor):
    data=form_data(visitor)
    with visitor.session_transaction() as s: copied=dict(s)
    def send():
        client=site.test_client()
        with client.session_transaction() as s: s.update(copied)
        return submit(client,'/apply',data).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: assert list(pool.map(lambda _:send(),range(2)))==[302,302]
    with site.app_context(): assert one('SELECT count(*) n FROM inquiries')['n']==1

def test_csrf_nonce_and_bot_protection(site,visitor):
    data=form_data(visitor)
    assert visitor.post('/apply',data=data).status_code==400
    data['submission_key']='forged'; assert submit(visitor,'/apply',data).status_code==400
    data=form_data(visitor,website='bot');assert submit(visitor,'/apply',data).status_code==400
    with site.app_context(): assert not one('SELECT id FROM inquiries')

@pytest.mark.parametrize('path',['/admin','/admin/inquiries/1','/admin/listings','/admin/listings/new','/admin/listings/1','/admin/stories','/admin/stories/1','/admin/content','/admin/archive'])
def test_admin_requires_operator(visitor,path):
    response=visitor.get(path)
    assert response.status_code==302 and response.location=='/admin/login'
    with visitor.session_transaction() as s: s.update(user_id=1,auth_version=1)
    assert visitor.get(path).location=='/admin/login'

@pytest.mark.parametrize('path',['/register','/profile','/apply/1','/applications/1','/inbox','/verify/token','/reset/token','/forgot-password','/admin/email','/admin/operations','/homes/1/availability','/homes/1/request'])
def test_old_workflows_removed(visitor,path): assert visitor.get(path).status_code==404

def test_participant_login_rejected_and_operator_logout(site,visitor):
    visitor.get('/admin/login')
    for email in ['guest@openestia.local','host@openestia.local']:
        assert submit(visitor,'/admin/login',dict(email=email,password=DEMO_PASSWORD)).status_code==401
    admin=operator(site)
    assert admin.get('/admin').status_code==200
    assert submit(admin,'/admin/logout',{}).status_code==302
    assert admin.get('/admin').location=='/admin/login'

def test_inquiry_notes_status_and_manual_contact_only(site,visitor):
    submit(visitor,'/apply',form_data(visitor)); admin=operator(site)
    assert submit(admin,'/admin/inquiries/1',dict(status='arranged',notes='PRIVATE NEW NOTE')).status_code==302
    html=admin.get('/admin/inquiries/1').get_data(as_text=True)
    assert 'https://wa.me/306912345678' in html and 'mailto:alex@example.test' in html
    assert 'PRIVATE NEW NOTE' in html and 'Arranged' in html
    for path in ['/','/explore','/homes/1','/journal','/thanks']:
        html=visitor.get(path).get_data(as_text=True)
        assert 'PRIVATE NEW NOTE' not in html and 'alex@example.test' not in html
    with site.app_context(): assert not one("SELECT 1 FROM sqlite_master WHERE name='outbox'")

def test_edit_publish_pause_listing_and_no_private_leak(site,visitor):
    admin=operator(site); payload=listing_payload()
    assert submit(admin,'/admin/listings/new',payload).status_code==302
    with site.app_context(): listing_id=one("SELECT id FROM listings WHERE name='Test Host'")['id']
    assert visitor.get('/homes/'+str(listing_id)).status_code==404
    payload['status']='published';payload['benefit_Meals']='conditional';payload['note_Meals']='Only when an event offers free food.'
    assert submit(admin,'/admin/listings/'+str(listing_id),payload).status_code==302
    html=visitor.get('/homes/'+str(listing_id)).get_data(as_text=True)
    assert 'Test Host' in html and 'Only when an event' in html and 'PRIVATE EXACT ADDRESS' not in html and 'PRIVATE OPERATOR NOTE' not in html
    data=form_data(visitor,listing_id=str(listing_id))
    payload['status']='paused';submit(admin,'/admin/listings/'+str(listing_id),payload)
    assert submit(visitor,'/apply',data).status_code==422
    assert 'Test Host' not in visitor.get('/explore').get_data(as_text=True)

def test_story_and_site_content_edit(site,visitor):
    admin=operator(site)
    story=dict(title='A verified new story',summary='Σύντομη σύνοψη.',city='Nairobi, Kenya',category='Builder story',published_on='2026-10-20',source_name='Original publisher',source_url='https://example.test/story',status='published',position='-1')
    assert submit(admin,'/admin/stories/new',story).status_code==302
    assert 'A verified new story' in visitor.get('/').get_data(as_text=True)
    with site.app_context(): values=settings(); story_id=one("SELECT id FROM stories WHERE title='A verified new story'")['id']
    values.update(hero_intro='Η δική μας καινούργια εισαγωγή.',contact_email='hello@example.test')
    assert submit(admin,'/admin/content',values).status_code==302
    assert values['hero_intro'] in visitor.get('/').get_data(as_text=True)
    assert 'mailto:hello@example.test' in visitor.get('/program').get_data(as_text=True)
    story['status']='paused';submit(admin,'/admin/stories/'+str(story_id),story)
    assert 'A verified new story' not in visitor.get('/journal').get_data(as_text=True)

def test_photo_validation_visibility_and_content(site,visitor):
    admin=operator(site);payload=listing_payload();payload.update(image_alt='A host photo',image_credit='Photo by owner',photo=(photo(),'host.png'))
    assert submit(admin,'/admin/listings/new',payload).status_code==302
    with site.app_context(): listing=one("SELECT * FROM listings WHERE name='Test Host'");image=listing['image'];listing_id=listing['id']
    image_url='/images/'+image[7:]
    assert visitor.get(image_url).status_code==404 and admin.get(image_url).status_code==200
    payload=listing_payload();payload.update(status='published',image_alt='A host photo',image_credit='Photo by owner')
    submit(admin,'/admin/listings/'+str(listing_id),payload)
    response=visitor.get(image_url);assert response.status_code==200 and response.mimetype=='image/webp'
    assert Image.open(io.BytesIO(response.data)).size==(64,40)
    payload['photo']=(io.BytesIO(b'<script>alert(1)</script>'),'malicious.png')
    assert submit(admin,'/admin/listings/'+str(listing_id),payload).status_code==422
    assert visitor.get('/images/../../secret.key').status_code==404

def test_xss_escaped_and_external_links_checked(site,visitor):
    data=form_data(visitor,name='<script>alert(1)</script>')
    assert submit(visitor,'/apply',data).status_code==302
    admin=operator(site);html=admin.get('/admin/inquiries/1').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html
    story=dict(title='Bad link',summary='Example',city='SF',category='News',published_on='2026-10-20',source_name='Source',source_url='javascript:alert(1)',status='published',position='0')
    assert submit(admin,'/admin/stories/new',story).status_code==422
    assert "default-src 'self'" in visitor.get('/').headers['Content-Security-Policy']

def test_rate_limit(site,visitor):
    visitor.get('/admin/login')
    for _ in range(10): assert submit(visitor,'/admin/login',dict(email='unknown@example.test',password='wrong')).status_code==401
    assert submit(visitor,'/admin/login',dict(email='unknown@example.test',password='wrong')).status_code==429

def test_seed_does_not_restore_operator_changes(site):
    from intake_seed import seed
    with site.app_context():
        execute("UPDATE listings SET name='Owner edited',status='paused' WHERE id=1")
        execute("DELETE FROM stories")
        execute("UPDATE site_settings SET value='My words' WHERE key='hero_intro'")
        seed()
        assert one('SELECT name FROM listings WHERE id=1')['name']=='Owner edited'
        assert not one('SELECT id FROM stories')
        assert settings()['hero_intro']=='My words'

def test_migrate_legacy_backup_without_mutation(tmp_path):
    from pathlib import Path
    SCHEMA=(Path(__file__).parent/"fixtures/previous_schema.sql").read_text()
    from werkzeug.security import generate_password_hash
    connection=sqlite3.connect(str(tmp_path/'open-estia.sqlite3'));connection.executescript(SCHEMA)
    password=generate_password_hash(DEMO_PASSWORD,method='pbkdf2:sha256:1000000')
    connection.execute("INSERT INTO users(id,email,password,name,role,created_at) VALUES(1,'admin@openestia.local',?,'Operator','admin','2026-01-01')",(password,))
    connection.execute("INSERT INTO users(id,email,password,name,role,created_at) VALUES(2,'host@example.test',?,'Host','host','2026-01-01')",(password,))
    connection.execute("INSERT INTO users(id,email,password,name,role,created_at) VALUES(3,'guest@example.test',?,'Guest','guest','2026-01-01')",(password,))
    connection.execute("INSERT INTO hosts(id,user_id,background,interests,motivation,builders,headline) VALUES(1,2,'Bio','Tech','Help','Builders','Hardware')")
    connection.execute("INSERT INTO homes(id,host_id,title,city,area,address,sleeping,shared,accessibility,rules,commitments,benefits,status) VALUES(1,1,'Title','SF','Area','PRIVATE ADDRESS','Couch','Kitchen','Steps','Quiet','None','{}','published')")
    connection.execute("INSERT INTO periods(id,home_id,start,end,capacity) VALUES(1,1,'2026-01-01','2026-01-15',1)")
    connection.execute("INSERT INTO applications(id,guest_id,period_id,start,end,background,project,links,outcome,reason,status,interview_notes,deadline,created_at,updated_at) VALUES(1,3,1,'2026-01-01','2026-01-15','Background','Project','','Outcome','Reason','offered','PRIVATE INTERVIEW','2026-01-01','2026-01-01','2026-01-01')")
    before={table:connection.execute('SELECT * FROM '+table).fetchall() for table in ['users','hosts','homes','periods','applications']}
    connection.commit();connection.close()
    migrated=create_app(dict(TESTING=True,DATA_DIR=str(tmp_path),SECRET_KEY='migration-test'))
    client=migrated.test_client();client.get('/')
    with migrated.app_context():
        for table,records in before.items(): assert [tuple(r) for r in rows('SELECT * FROM '+table)]==records
        item=one('SELECT * FROM inquiries');assert item['status']=='contacted' and item['notes']=='PRIVATE INTERVIEW'
        assert json.loads(item['legacy_json'])['status']=='offered'
        assert one('SELECT count(*) n FROM operators')['n']==1
    create_app(dict(TESTING=True,DATA_DIR=str(tmp_path),SECRET_KEY='migration-test'))
    with migrated.app_context(): assert one('SELECT count(*) n FROM inquiries')['n']==1
    admin=operator(migrated)
    assert 'PRIVATE INTERVIEW' in admin.get('/admin/inquiries/1').get_data(as_text=True)
    archive=admin.get('/admin/archive?table=users').get_data(as_text=True)
    assert password not in archive and 'guest@example.test' in archive
    assert admin.get('/admin/archive?table=tokens').status_code==404
    assert 'PRIVATE ADDRESS' not in client.get('/homes/1').get_data(as_text=True)


def test_backup_reset_restore_commands(site,visitor):
    import os
    import subprocess
    import sys
    from pathlib import Path
    submit(visitor,'/apply',form_data(visitor))
    data=Path(site.config['DATA_DIR'])
    (data/'uploads'/'retained-example.txt').write_text('private backup evidence')
    env=dict(os.environ,OPEN_ESTIA_DATA_DIR=str(data))
    env.pop('OPEN_ESTIA_SECRET_KEY',None)
    root=Path(__file__).resolve().parents[1]
    def run(*args):
        result=subprocess.run([sys.executable,'manage.py',*args],cwd=str(root),env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
        return result.stdout
    run('backup')
    snapshot=sorted((data/'backups').glob('backup-*'))[-1]
    original_key=(data/'secret.key').read_text()
    run('reset','--confirm','RESET-SAMPLE-DATA')
    with site.app_context(): assert not one('SELECT id FROM inquiries')
    assert not (data/'uploads'/'retained-example.txt').exists()
    assert (data/'secret.key').read_text()!=original_key
    run('restore','--backup',str(snapshot),'--confirm','RESTORE-BACKUP')
    with site.app_context(): assert one('SELECT count(*) n FROM inquiries')['n']==1
    assert (data/'uploads'/'retained-example.txt').read_text()=='private backup evidence'

def test_admin_post_authentication_csrf_and_changed_credentials(site,visitor):
    visitor.get('/')
    assert submit(visitor,'/admin/listings/new',listing_payload()).location=='/admin/login'
    admin=operator(site)
    assert admin.post('/admin/listings/new',data=listing_payload()).status_code==400
    with site.app_context(): execute('UPDATE operators SET auth_version=auth_version+1')
    assert admin.get('/admin').location=='/admin/login'


def test_malformed_csrf_is_rejected_without_server_error(visitor):
    visitor.get('/apply')
    response=visitor.post('/apply',data={'csrf':'δοκιμή'})
    assert response.status_code==400
    assert 'φόρμα έληξε' in response.get_data(as_text=True)

@pytest.mark.parametrize('field',['adult','consent'])
def test_explicit_false_confirmation_cannot_be_recorded_as_agreement(site,visitor,field):
    data=form_data(visitor)
    data[field]='0'
    response=submit(visitor,'/apply',data)
    assert response.status_code==422
    checkbox=re.search(r'<input[^>]+name="'+field+r'"[^>]*>',response.get_data(as_text=True)).group(0)
    assert 'checked' not in checkbox
    with site.app_context(): assert not one('SELECT id FROM inquiries')

def test_valid_long_benefits_remain_editable(site):
    admin=operator(site);payload=listing_payload()
    for key in ('Meals','Gym access','Workspace','Mentorship','Introductions'):
        payload['benefit_'+key]='conditional'
        payload['note_'+key]='A detailed agreed condition. '*60
    assert submit(admin,'/admin/listings/new',payload).status_code==302
    with site.app_context():
        listing=one("SELECT * FROM listings WHERE name='Test Host'")
        assert len(listing['benefits'])>6000
        listing_id=listing['id']
    payload['name']='Updated host name'
    assert submit(admin,'/admin/listings/'+str(listing_id),payload).status_code==302
    with site.app_context():
        listing=one('SELECT * FROM listings WHERE id=?',(listing_id,))
        assert listing['name']=='Updated host name'
        assert json.loads(listing['benefits'])['Meals']['note']==payload['note_Meals'].strip()
