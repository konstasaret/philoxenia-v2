import json
from werkzeug.security import generate_password_hash
from store import one, execute, insert, atomic, stamp
from sample_content import SAMPLE_HOSTS

DEMO_EMAIL='admin@greekmafia.local'
DEMO_PASSWORD='GreekMafiaDemo!2026'
DEFAULT_CONTENT={'hero_intro': 'Θέλουμε να χτίσουμε τη μεγαλύτερη και πιο επιτυχημένη ελληνική «μαφία» στον κόσμο. Μια απολύτως νόμιμη '
               'οικογένεια ανθρώπων που δημιουργούν, ανεβαίνουν και τραβούν ο ένας τον άλλο πιο ψηλά. Από την Ελλάδα, '
               'σε κάθε μέρος όπου συμβαίνουν μεγάλα πράγματα.',
 'manifesto': 'Κι εμείς βρεθήκαμε κάποτε μέσα σε μια τέτοια «μαφία»: μια παρέα που μας έκανε χώρο, μοιράστηκε όσα '
              'ήξερε και πίστεψε σε εμάς πριν έχουμε πολλά να δείξουμε. Αυτή η εμπειρία άλλαξε το τι θεωρούσαμε εφικτό '
              'για τη ζωή μας.',
 'origin': 'Η Philoxenia by Hustle Hours άναψε τη σπίθα: άνθρωποι που ανοίγουν τον χώρο και τον κόσμο τους σε νέους '
           'builders. Με σεβασμό σε αυτό που ξεκίνησαν, θέλουμε να μεταφέρουμε τη φλόγα παντού. Η Greek Mafia είναι η '
           'δική μας ανεξάρτητη προσπάθεια να γίνει αυτή η νοοτροπία ένα παγκόσμιο ελληνικό δίκτυο.',
 'guest_intro': 'Associate σημαίνει νέο μέλος της οικογένειας. Πες μας τι χτίζεις, πού θέλεις να φτάσεις και πώς '
                'θέλεις να εξελιχθείς. Δεν χρειάζεται να έχεις όλες τις απαντήσεις. Χρειάζεται να θέλεις να κάνεις τη '
                'δουλειά και, όταν μπορείς, να βοηθήσεις τον επόμενο.',
 'host_intro': 'Godfather είναι ο άνθρωπος που βοηθά κάποιον άλλον να κάνει το επόμενο βήμα. Γνώση, feedback, '
               'γνωριμίες, βοήθεια στην πόλη ή και ένας καναπές. Πες μας τι μπορείς πραγματικά να προσφέρεις. Δεν '
               'χρειάζεται να διαθέτεις σπίτι. Ο ρόλος είναι ανοιχτός σε όλα τα φύλα.',
 'contact_email': ''}

# Upgrade only untouched previous defaults; preserve operator-authored copy.
PREVIOUS_CONTENT={'hero_intro': 'Οι Έλληνες είμαστε παντού. Ας είμαστε και ο ένας δίπλα στον άλλο. Το Open Estia θέλει να μας φέρει '
               'κοντά, για να μοιραζόμαστε χώρο, εμπειρία και χρόνο — και να προχωράμε μαζί.',
 'manifesto': 'Αν χτίζεις κάτι, ίσως αυτό που σου λείπει είναι να ονειρευτείς λίγο μεγαλύτερα. Να δεις από κοντά '
              'ανθρώπους που έχουν ήδη κάνει μερικά από τα βήματα που σκέφτεσαι. Και τι καλύτερο από το να ζήσεις για '
              'λίγο μαζί τους;',
 'origin': 'Για εμάς, η σπίθα ήταν η Philoxenia by Hustle Hours. Ο Ντίνος και ο Τάκης περιγράφουν πώς ξεκίνησαν με το '
           'όνειρο να βρεθούν στο San Francisco και πόσο δύσκολο ήταν να αποκτήσουν πρόσβαση σε αυτόν τον κόσμο. Η '
           'πρωτοβουλία τους μας ενέπνευσε. Θέλουμε να μεταφέρουμε αυτή τη φλόγα παντού, με τη δική μας προσπάθεια.',
 'guest_intro': 'Πες μας τι χτίζεις, τι θέλεις να μάθεις και πού θα ήθελες να πας. Γράψε όπως θα μας τα έλεγες από '
                'κοντά. Θα διαβάσουμε την αίτησή σου και θα συνεχίσουμε προσωπικά, με email ή WhatsApp.',
 'host_intro': 'Μπορεί να έχεις έναν καναπέ, ένα δωμάτιο και λίγο χρόνο για έναν άνθρωπο που ξεκινά. Δεν χρειάζεται '
               'κάτι εντυπωσιακό. Πες μας για εσένα και θα μιλήσουμε πριν δημοσιευτεί οτιδήποτε.',
 'contact_email': ''}

STORIES=[
 dict(title='The first engineer. A whole new chapter.',city='San Francisco, USA',category='Builder story',published_on='2026-10-20',source_name='Y Combinator',
      summary='Ο Vin Bui μπήκε στη Nowadays ως ο πρώτος engineer. Η ιστορία του για την ευθύνη, την αυτονομία και το να χτίζεις μαζί με ανθρώπους που εμπιστεύεσαι.',
      source_url='https://www.ycombinator.com/blog/how-vin-bui-became-engineer-1-at-nowadays-and-started-treating-it-like-his-own-company',
      image='builders-nowadays.jpeg',image_alt='Φωτογραφία από την ιστορία του Vin Bui και της Nowadays',image_credit='Nowadays / Y Combinator',position=0),
 dict(title='New ground for European builders.',city='Munich, Germany',category='Startup news',published_on='2026-09-28',source_name='Mistral',
      summary='Η Mistral ανακοίνωσε ένα νέο hub στο Μόναχο, με ομάδες έρευνας και μηχανικούς που δουλεύουν πάνω σε εφαρμογές AI για τη βιομηχανία.',
      source_url='https://mistral.ai/news/hallo-deutschland/',image='builders-mistral.webp',image_alt='Εικόνα από την ανακοίνωση της Mistral για το νέο hub στο Μόναχο',image_credit='Mistral',position=1),
 dict(title='From four founders to a public company.',city='Bengaluru, India',category='From the archive',published_on='2025-11-12',source_name='Y Combinator',
      summary='Τον Νοέμβριο του 2025, η Groww έγινε η πρώτη εταιρεία του YC που μπήκε στο χρηματιστήριο στην Ινδία. Μια ιστορία για το να ξεκινάς τοπικά και να συνεχίζεις με υπομονή.',
      source_url='https://www.ycombinator.com/blog/groww/',image='builders-groww.png',image_alt='Οι ιδρυτές της Groww στο βίντεο της αίτησής τους στο YC το 2018',image_credit='Groww / Y Combinator · 2018',position=2),
]


def seed():
    with atomic():
        for key,value in DEFAULT_CONTENT.items():
            execute('INSERT OR IGNORE INTO site_settings VALUES(?,?)',(key,value))
        if not one("SELECT 1 FROM site_settings WHERE key='greek_mafia_copy_v1'"):
            for key,previous in PREVIOUS_CONTENT.items():
                if key!='contact_email':
                    execute('UPDATE site_settings SET value=? WHERE key=? AND value=?',(DEFAULT_CONTENT[key],key,previous))
            execute("INSERT INTO site_settings VALUES('greek_mafia_copy_v1','1')")
        if not one('SELECT 1 FROM operators'):
            insert('operators',dict(email=DEMO_EMAIL,name='Greek Mafia operator',password=generate_password_hash(DEMO_PASSWORD,method='pbkdf2:sha256:1000000')))
        if not one("SELECT 1 FROM site_settings WHERE key='directory_seeded'"):
            if not one('SELECT 1 FROM listings'):
                for i,(email,h) in enumerate(SAMPLE_HOSTS.items()):
                    sf='host.sf@' in email
                    benefits={
                     'Workspace':{'status':'included','note':'Κοινό τραπέζι και Wi-Fi.'},
                     'Mentorship':{'status':'included' if sf else 'conditional','note':h['support']},
                     'Meals':{'status':'conditional','note':h['meals']},
                     'Gym access':{'status':'conditional' if sf else 'unavailable','note':'Guest pass μόνο εφόσον το επιτρέπει το γυμναστήριο και υπάρχει διαθέσιμο pass.' if sf else 'Δεν προσφέρεται.'},
                     'Introductions':{'status':'conditional','note':'Με συναίνεση και διαθέσιμο χρόνο. Δεν εγγυώνται απάντηση ή επαγγελματική ευκαιρία.'}}
                    insert('listings',dict(name=h['name'],headline=h['headline'],city=['Lisbon','Berlin','San Francisco'][i],background=h['background'],
                        sleeping=h['sleeping'],accessibility=h['accessibility'],shared='Κοινόχρηστη κουζίνα και μπάνιο.',rules='Σεβασμός στον χώρο, στην ησυχία και στην ιδιωτικότητα.',
                        commitments='Συμφωνούμε τις λεπτομέρειες πριν τη διαμονή. Χωρίς ανταλλάγματα ή υποχρέωση εργασίας.',benefits=json.dumps(benefits,ensure_ascii=False),
                        availability='Οι ημερομηνίες συμφωνούνται προσωπικά.',status='published',sample=1,position=0 if sf else i+1,updated_at=stamp()))
            execute("INSERT INTO site_settings VALUES('directory_seeded','1')")
        if not one("SELECT 1 FROM site_settings WHERE key='journal_seeded'"):
            for story in STORIES: insert('stories',dict(story,status='published'))
            execute("INSERT INTO site_settings VALUES('journal_seeded','1')")
