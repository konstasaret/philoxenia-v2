"""Public inquiry forms and a private operator workspace. No participant accounts."""
import hashlib
import io
import json
import os
import re
import secrets
import warnings
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import quote, urlsplit

from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from store import atomic, close_db, db, execute, init_db, insert, one, rows, settings, stamp, update
from intake_seed import DEFAULT_CONTENT, seed
from brand import display_content
from sample_content import BENEFIT_LABELS

ROOT=Path(__file__).resolve().parent
STATES={'new':'New','contacted':'Contacted','arranged':'Arranged','closed':'Closed'}
BENEFITS=('Meals','Gym access','Workspace','Mentorship','Introductions')
PUBLISH_STATES=('draft','published','paused')
DUMMY_HASH=generate_password_hash('unusable-demo-dummy-password',method='pbkdf2:sha256:1000000')


def public_url(value):
    try:
        parsed=urlsplit(value)
        return parsed.scheme in ('http','https') and bool(parsed.hostname) and not parsed.username and not parsed.password and not any(c.isspace() or ord(c)<32 for c in value)
    except ValueError:
        return False


def create_app(test_config=None):
    env=ROOT/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('OPEN_ESTIA_') and '=' in line:
                key,value=line.split('=',1)
                os.environ.setdefault(key.strip(),value.strip().strip('\"\''))
    app=Flask(__name__)
    data=Path(os.getenv('OPEN_ESTIA_DATA_DIR',str(ROOT/'.data')))
    if not data.is_absolute(): data=ROOT/data
    if test_config and 'DATA_DIR' in test_config: data=Path(test_config['DATA_DIR'])
    data.mkdir(parents=True,exist_ok=True,mode=0o700)
    (data/'uploads').mkdir(exist_ok=True,mode=0o700)
    secret_path=data/'secret.key'
    if not secret_path.exists():
        try:
            with secret_path.open('x') as f: f.write(secrets.token_hex(48))
            secret_path.chmod(0o600)
        except FileExistsError: pass
    app.config.update(SECRET_KEY=os.getenv('OPEN_ESTIA_SECRET_KEY') or secret_path.read_text().strip(),
        DATA_DIR=str(data),DATABASE=str(data/'open-estia.sqlite3'),BASE_URL=os.getenv('OPEN_ESTIA_BASE_URL','http://127.0.0.1:5073').rstrip('/'),
        SESSION_COOKIE_NAME='open_estia_operator',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('OPEN_ESTIA_COOKIE_SECURE','0')=='1',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=int(os.getenv('OPEN_ESTIA_SESSION_HOURS','8'))),
        MAX_CONTENT_LENGTH=8*1024*1024,TRUSTED_HOSTS=['127.0.0.1','localhost','[::1]'],SEED=True)
    if test_config: app.config.update(test_config)
    if not re.fullmatch(r'http://(localhost|127\.0\.0\.1)(:\d+)?',app.config['BASE_URL']):
        raise RuntimeError('Local-only mode requires a localhost BASE_URL.')
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
        if app.config['SEED']: seed()

    @app.before_request
    def before():
        g.operator=None
        if session.get('operator_id'):
            operator=one('SELECT * FROM operators WHERE id=?',(session['operator_id'],))
            if operator and operator['auth_version']==session.get('auth_version'): g.operator=operator
            else: session.clear()
        session.setdefault('csrf',secrets.token_urlsafe(32))
        if request.method=='POST' and not secrets.compare_digest(session['csrf'].encode('utf-8'),request.form.get('csrf','').encode('utf-8')):
            abort(400,'Η φόρμα έληξε. Άνοιξε ξανά τη σελίδα και δοκίμασε πάλι.')

    @app.after_request
    def headers(response):
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'; object-src 'none'"
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        if request.endpoint!='static': response.headers['Cache-Control']='no-store'
        return response

    def image_url(value):
        if not value: return ''
        if value.startswith('upload:'): return url_for('uploaded_image',filename=value[7:])
        return url_for('static',filename='images/'+value)

    @app.context_processor
    def context():
        return dict(operator=g.operator,csrf=session['csrf'],content=display_content(settings(),DEFAULT_CONTENT),states=STATES,
            role_labels={'guest':'Associate','host':'Godfather','support':'Previous report'},benefit_names=BENEFIT_LABELS,benefit_keys=BENEFITS,parse_json=json.loads,image_url=image_url,
            is_admin=request.path.startswith('/admin'),valid_url=public_url,
            date_label=lambda value:date.fromisoformat(value[:10]).strftime('%d %b %Y') if value else '')

    @app.errorhandler(HTTPException)
    def error(err):
        return render_template('v2/error.html',error=err),err.code

    def operator_only(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not g.operator: return redirect(url_for('admin_login'))
            return fn(*args,**kwargs)
        return wrapped

    def limited(bucket,maximum):
        key=hashlib.sha256((bucket+'|'+(request.remote_addr or '')).encode()).hexdigest()
        now=datetime.now(timezone.utc)
        with atomic():
            r=one('SELECT * FROM intake_limits WHERE key=?',(key,))
            if r and r['until']>now.isoformat():
                if r['count']>=maximum: abort(429,'Πολλές προσπάθειες. Δοκίμασε ξανά σε 15 λεπτά.')
                execute('UPDATE intake_limits SET count=count+1 WHERE key=?',(key,))
            else: execute('INSERT OR REPLACE INTO intake_limits VALUES(?,?,?)',(key,1,(now+timedelta(minutes=15)).isoformat()))

    def published_listings(): return rows("SELECT * FROM listings WHERE status='published' ORDER BY position,id")

    @app.get('/')
    def index(): return render_template('v2/index.html',listings=published_listings())

    @app.get('/explore')
    @app.get('/godfathers')
    def explore():
        city=request.args.get('city','').strip()
        published=published_listings()
        listings=[h for h in published if not city or h['city']==city]
        return render_template('v2/explore.html',listings=listings,city=city,cities=sorted({h['city'] for h in published if h['city'].strip()}))

    @app.get('/homes/<int:listing_id>')
    @app.get('/godfathers/<int:listing_id>')
    def home(listing_id):
        listing=one('SELECT * FROM listings WHERE id=?',(listing_id,))
        if not listing or listing['status']!='published': abort(404)
        return redirect(url_for('explore',_anchor='godfather-'+str(listing_id)))

    @app.get('/journal')
    def journal(): return redirect(url_for('index'))

    def new_form_key():
        token=secrets.token_urlsafe(32)
        session['form_keys']=(session.get('form_keys',[])+[token])[-12:]
        return token

    def inquiry_form(kind):
        choices=published_listings()
        values=request.form.to_dict() if request.method=='POST' else {'listing_id':request.args.get('host','')}
        errors={}
        token=values.get('submission_key') if request.method=='POST' else new_form_key()
        if request.method=='POST':
            if token not in session.get('form_keys',[]): abort(400,'Άνοιξε ξανά τη φόρμα και δοκίμασε πάλι.')
            if one('SELECT id FROM inquiries WHERE submission_key=?',(token,)):
                session['submitted_kind']=kind
                return redirect(url_for('thanks'))
            limited('inquiry',20)
            if values.get('website'): abort(400,'Δεν ήταν δυνατή η αποστολή.')
            for key,label,minimum,maximum in [('name','Το όνομά σου',2,120),('email','Email',3,254),('message','Το pitch σου',10,5000)]:
                values[key]=values.get(key,'').strip()
                if not minimum<=len(values[key])<=maximum: errors[key]=label+': συμπλήρωσε από '+str(minimum)+' έως '+str(maximum)+' χαρακτήρες.'
            if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",values.get('email','')): errors['email']='Γράψε ένα έγκυρο email.'
            phone=values.get('phone','').strip()
            normalized=re.sub(r'[ ()-]','',phone)
            if not re.fullmatch(r'\+[1-9]\d{6,14}',normalized): errors['phone']='Πρόσθεσε τον κωδικό χώρας, π.χ. +30 691 234 5678.'
            for key,maximum in [('city',120),('dates',200),('links',1500)]:
                values[key]=values.get(key,'').strip()
                if len(values[key])>maximum: errors[key]='Το κείμενο είναι πολύ μεγάλο.'
            links=values.get('links','').splitlines()
            if len(links)>5 or any(not public_url(link.strip()) for link in links if link.strip()): errors['links']='Βάλε έως 5 πλήρη links, ένα ανά γραμμή (https://…).'
            if values.get('adult')!='1': errors['adult']='Η κοινότητα είναι για ενήλικες 18+.'
            if values.get('consent')!='1': errors['consent']='Χρειαζόμαστε τη συγκατάθεσή σου για να επικοινωνήσουμε.'
            selected=None
            if kind=='guest' and values.get('listing_id'):
                selected=one("SELECT * FROM listings WHERE id=? AND status='published'",(values['listing_id'],))
                if not selected: errors['listing_id']='Αυτό το προφίλ δεν είναι πλέον διαθέσιμο. Διάλεξε άλλο ή άφησε την επιλογή κενή.'
            if kind=='host' and not values.get('city'): errors['city']='Σε ποια πόλη μπορείς να στηρίξεις ένα νέο μέλος;'
            if not errors:
                moment=stamp()
                with atomic():
                    # Recheck under the same write lock as insertion; pausing a host cannot race a submission.
                    if selected and not one("SELECT 1 FROM listings WHERE id=? AND status='published'",(selected['id'],)): abort(409,'Το προφίλ μόλις άλλαξε. Δοκίμασε ξανά.')
                    if not one('SELECT id FROM inquiries WHERE submission_key=?',(token,)):
                        insert('inquiries',dict(kind=kind,name=values['name'],email=values['email'].lower(),phone=normalized,
                            listing_id=selected['id'] if selected else None,listing_label=(selected['name']+' · '+selected['city']) if selected else '',
                            city=values.get('city',''),dates=values.get('dates',''),message=values['message'],links=values.get('links',''),adult=1,
                            consent_at=moment,submission_key=token,created_at=moment,updated_at=moment))
                session['submitted_kind']=kind
                return redirect(url_for('thanks'))
        return render_template('v2/form.html',kind=kind,values=values,errors=errors,submission_key=token,listings=choices),422 if errors else 200

    @app.route('/apply',methods=['GET','POST'])
    @app.route('/join',methods=['GET','POST'])
    def apply(): return inquiry_form('guest')

    @app.route('/become-a-host',methods=['GET','POST'])
    @app.route('/become-a-godfather',methods=['GET','POST'])
    def become_host(): return inquiry_form('host')

    @app.get('/thanks')
    def thanks():
        if not session.get('submitted_kind'): return redirect(url_for('apply'))
        return render_template('v2/thanks.html',kind=session['submitted_kind'])

    @app.get('/program')
    def program(): return render_template('v2/program.html')

    @app.route('/admin/login',methods=['GET','POST'])
    def admin_login():
        if g.operator: return redirect(url_for('admin'))
        error=''
        if request.method=='POST':
            limited('operator-login',10)
            email=request.form.get('email','').strip().lower()
            operator=one('SELECT * FROM operators WHERE email=?',(email,))
            password=request.form.get('password','')
            ok=check_password_hash(operator['password'] if operator else DUMMY_HASH,password[:129])
            if operator and ok and len(password)<=128:
                session.clear()
                session.update(operator_id=operator['id'],auth_version=operator['auth_version'],csrf=secrets.token_urlsafe(32))
                session.permanent=True
                return redirect(url_for('admin'))
            error='The email or password is incorrect.'
        return render_template('v2/login.html',error=error),401 if error else 200

    @app.post('/admin/logout')
    @operator_only
    def admin_logout():
        session.clear()
        return redirect(url_for('index'))

    @app.get('/admin')
    @operator_only
    def admin():
        kind=request.args.get('kind',''); status=request.args.get('status',''); search=request.args.get('q','').strip()[:150]
        inquiries=rows("SELECT * FROM inquiries WHERE (?='' OR kind=?) AND (?='' OR status=?) AND (?='' OR instr(lower(name||' '||email||' '||message),lower(?))>0) ORDER BY created_at DESC,id DESC",(kind,kind,status,status,search,search))
        counts={r['status']:r['n'] for r in rows('SELECT status,count(*) n FROM inquiries GROUP BY status')}
        return render_template('v2/admin.html',inquiries=inquiries,counts=counts,kind=kind,status=status,search=search)

    @app.route('/admin/inquiries/<int:inquiry_id>',methods=['GET','POST'])
    @operator_only
    def inquiry(inquiry_id):
        item=one('SELECT * FROM inquiries WHERE id=?',(inquiry_id,))
        if not item: abort(404)
        if request.method=='POST':
            status=request.form.get('status',''); notes=request.form.get('notes','').strip()
            if status not in STATES or len(notes)>20000: abort(400,'Choose a valid status and keep notes under 20,000 characters.')
            with atomic(): update('inquiries',inquiry_id,dict(status=status,notes=notes,updated_at=stamp()))
            flash('Saved. No message was sent.','success')
            return redirect(url_for('inquiry',inquiry_id=inquiry_id))
        phone=re.sub(r'\D','',item['phone'])
        return render_template('v2/inquiry.html',item=item,legacy=json.loads(item['legacy_json']),
            email_link='mailto:'+quote(item['email'],safe='@')+'?subject='+quote('The Godfather · '+item['name']),
            whatsapp_link='https://wa.me/'+phone if phone else '')

    def editor_values(keys): return {k:request.form.get(k,'').strip() for k in keys}

    def validate_editor(values,required):
        errors={}
        for key in required:
            if not values.get(key): errors[key]='This field is required.'
        for key,value in values.items():
            # Benefit notes have their own per-note limit below; their stored JSON
            # must not make a valid listing impossible to edit on the next visit.
            if key!='benefits' and isinstance(value,str) and len(value)>6000: errors[key]='Keep this field under 6,000 characters.'
        if values.get('status') not in PUBLISH_STATES: errors['status']='Choose draft, published or paused.'
        try:
            values['position']=int(values.get('position',0))
            if not -1000<=values['position']<=10000: raise ValueError
        except (ValueError,TypeError): errors['position']='Use a whole number from -1000 to 10000.'
        return errors

    def upload_image(values,errors):
        uploaded=request.files.get('photo')
        if not uploaded or not uploaded.filename: return
        if not values.get('image_alt') or not values.get('image_credit'):
            errors['photo']='Add an image description and credit before uploading.'
            return
        if errors: return
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                image=Image.open(uploaded.stream)
                if image.format not in ('JPEG','PNG','WEBP') or image.width*image.height>20000000: raise ValueError
                image.load()
                image=ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((1800,1800))
                output=io.BytesIO(); image.save(output,format='WEBP',quality=88)
            filename=secrets.token_hex(20)+'.webp'
            path=Path(app.config['DATA_DIR'])/'uploads'/filename
            path.write_bytes(output.getvalue()); path.chmod(0o600)
            values['image']='upload:'+filename
        except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
            errors['photo']='Choose a JPEG, PNG or WebP image under 20 megapixels and 8 MB.'

    @app.get('/admin/listings')
    @operator_only
    def admin_listings(): return render_template('v2/entries.html',kind='listings',entries=rows('SELECT * FROM listings ORDER BY position,id'))

    @app.route('/admin/listings/new',methods=['GET','POST'],defaults={'listing_id':None})
    @app.route('/admin/listings/<int:listing_id>',methods=['GET','POST'])
    @operator_only
    def edit_listing(listing_id):
        saved=one('SELECT * FROM listings WHERE id=?',(listing_id,)) if listing_id else None
        if listing_id and not saved: abort(404)
        values=dict(saved) if saved else dict(status='draft',position=10,benefits='{}',sample=0)
        errors={}
        if request.method=='POST':
            values.update(editor_values(('name','headline','city','area','background','sleeping','shared','accessibility','rules','commitments','availability','status','position','contact_email','contact_phone','address','private_notes','image_alt','image_credit','linkedin_url')))
            values['sample']=int(request.form.get('sample')=='1')
            errors=validate_editor(values,('name','headline','city','background','availability'))
            if values.get('linkedin_url') and (not public_url(values['linkedin_url']) or urlsplit(values['linkedin_url']).scheme!='https' or urlsplit(values['linkedin_url']).hostname not in ('linkedin.com','www.linkedin.com') or not urlsplit(values['linkedin_url']).path.startswith('/in/')):
                errors['linkedin_url']='Use a complete https://www.linkedin.com/in/ profile link.'
            if values.get('status')=='published' and not values.get('sleeping'):
                errors['sleeping']='Describe the air mattress, couch or room before publishing this Godfather.'
            benefits={}
            for key in BENEFITS:
                state=request.form.get('benefit_'+key,'unavailable')
                note=request.form.get('note_'+key,'').strip()
                if state not in ('included','conditional','unavailable') or len(note)>2000 or (state!='unavailable' and not note):
                    errors['benefits']='Every included or conditional benefit needs a description; keep each under 2,000 characters.'
                benefits[key]=dict(status=state,note=note)
            values['benefits']=json.dumps(benefits,ensure_ascii=False)
            if request.form.get('remove_image'): values['image']=''
            upload_image(values,errors)
            if not errors:
                values.pop('id',None); values['updated_at']=stamp()
                with atomic():
                    if listing_id: update('listings',listing_id,values)
                    else: listing_id=insert('listings',values)
                flash('Listing saved. Published listings appear on the website immediately.','success')
                return redirect(url_for('admin_listings'))
        return render_template('v2/listing_edit.html',values=values,errors=errors,listing_id=listing_id),422 if errors else 200

    @app.get('/admin/stories')
    @operator_only
    def admin_stories(): return render_template('v2/entries.html',kind='stories',entries=rows('SELECT * FROM stories ORDER BY position,id'))

    @app.route('/admin/stories/new',methods=['GET','POST'],defaults={'story_id':None})
    @app.route('/admin/stories/<int:story_id>',methods=['GET','POST'])
    @operator_only
    def edit_story(story_id):
        saved=one('SELECT * FROM stories WHERE id=?',(story_id,)) if story_id else None
        if story_id and not saved: abort(404)
        values=dict(saved) if saved else dict(status='draft',position=10,category='Builder story',published_on=date.today().isoformat())
        errors={}
        if request.method=='POST':
            values.update(editor_values(('title','summary','city','category','published_on','source_name','source_url','image_alt','image_credit','status','position')))
            errors=validate_editor(values,('title','summary','city','category','published_on','source_name','source_url'))
            if not public_url(values['source_url']): errors['source_url']='Use a complete https:// source link.'
            try: date.fromisoformat(values['published_on'])
            except ValueError: errors['published_on']='Use a real publication date.'
            if request.form.get('remove_image'): values['image']=''
            upload_image(values,errors)
            if not errors:
                values.pop('id',None)
                with atomic():
                    if story_id: update('stories',story_id,values)
                    else: story_id=insert('stories',values)
                flash('Story saved.','success')
                return redirect(url_for('admin_stories'))
        return render_template('v2/story_edit.html',values=values,errors=errors,story_id=story_id),422 if errors else 200

    @app.route('/admin/content',methods=['GET','POST'])
    @operator_only
    def admin_content():
        values=settings(); errors={}
        if request.method=='POST':
            values=editor_values(DEFAULT_CONTENT)
            for key,value in values.items():
                if len(value)>3000 or (key!='contact_email' and not value): errors[key]='Use 1–3,000 characters.'
            if values['contact_email'] and not re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',values['contact_email']): errors['contact_email']='Use a valid contact email.'
            if not errors:
                with atomic():
                    for key,value in values.items(): execute('INSERT OR REPLACE INTO site_settings VALUES(?,?)',(key,value))
                flash('Website copy saved.','success')
                return redirect(url_for('admin_content'))
        return render_template('v2/content_edit.html',values=values,errors=errors),422 if errors else 200

    @app.get('/images/<filename>')
    def uploaded_image(filename):
        if not re.fullmatch(r'[a-f0-9]{40}\.webp',filename): abort(404)
        image='upload:'+filename
        allowed=g.operator or one("SELECT 1 FROM listings WHERE image=? AND status='published'",(image,)) or one("SELECT 1 FROM stories WHERE image=? AND status='published'",(image,))
        path=Path(app.config['DATA_DIR'])/'uploads'/filename
        if not allowed or not path.is_file(): abort(404)
        return send_file(path,mimetype='image/webp',conditional=False)

    # Historical information stays operator-only; credentials and reset tokens are never rendered.
    archive_columns={
        'applications':'id,guest_id,period_id,start,end,status,background,project,links,outcome,reason,interview_notes,host_summary,interview_link,request_text,answer,host_reason,terms,deadline,created_at,updated_at',
        'users':'id,email,name,role,verified,adult,eligibility,background,project,links,created_at',
        'hosts':'id,user_id,background,interests,motivation,builders,review_label,sample,headline',
        'homes':'id,host_id,title,city,area,address,sleeping,shared,accessibility,rules,commitments,benefits,status,sample',
        'periods':'id,home_id,start,end,capacity,active',
        'events':'id,actor_id,application_id,kind,detail,created_at',
        'host_submissions':'id,name,email,city,background,proposal,status,created_at',
        'reports':'id,user_id,contact,detail,status,resolution,created_at',
        'outbox':'id,recipient,template,subject,body,status,error,attempts,created_at,delivered_at',
    }

    @app.get('/admin/archive')
    @operator_only
    def archive():
        existing={r['name'] for r in rows("SELECT name FROM sqlite_master WHERE type='table'")}
        available=[t for t in archive_columns if t in existing]
        selected=request.args.get('table',available[0] if available else '')
        if selected and selected not in available: abort(404)
        records=rows('SELECT '+archive_columns[selected]+' FROM '+selected+' ORDER BY id DESC') if selected else []
        return render_template('v2/archive.html',tables=available,selected=selected,records=records)

    @app.get('/login')
    def old_login(): return redirect(url_for('admin_login'))

    @app.get('/dashboard')
    def old_dashboard(): return redirect(url_for('admin'))

    return app


if __name__=='__main__':
    create_app().run(host='127.0.0.1',port=int(os.getenv('OPEN_ESTIA_PORT','5073')),debug=False)
