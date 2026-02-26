from flask import Flask, g, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import secrets
import bleach
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

DB_PATH = 'data.db'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', secrets.token_hex(16))
csrf = CSRFProtect()
csrf.init_app(app)


@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf, csp_nonce=lambda: getattr(g, 'csp_nonce', ''))


def allowed_image_file(filename):
    ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS


def save_upload_file(file, max_size_bytes=4*1024*1024):
    if not file or not file.filename:
        return None
    if not allowed_image_file(file.filename):
        return None
    if file.content_length and file.content_length > max_size_bytes:
        return None
    # generate safe unique name using hash
    import hashlib
    ext = secure_filename(file.filename).rsplit('.', 1)[1] if '.' in secure_filename(file.filename) else 'tmp'
    hash_name = hashlib.sha256(file.read()).hexdigest()[:16]
    file.seek(0)
    filename = f"{hash_name}.{ext}"
    relpath = os.path.join('uploads', filename)
    savepath = os.path.join('static', relpath)
    file.save(savepath)
    return '/static/' + relpath.replace('\\','/')


@app.route('/admin/upload_image', methods=['POST'])
@admin_required
def admin_upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    url = save_upload_file(file)
    if url:
        return jsonify({'location': url})
    return jsonify({'error': 'Invalid file'}), 400




def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    cur = db.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        grade INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        starred INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        html TEXT,
        link TEXT,
        categories TEXT,
        grades TEXT,
        author_id INTEGER,
        FOREIGN KEY(author_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER,
        action TEXT
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    ''')
    db.commit()
    # try to add role column to users table (for upgrades)
    try:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        db.commit()
    except sqlite3.OperationalError:
        pass


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def ensure_default_admin():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM users WHERE username=?', ('228820',))
    if not cur.fetchone():
        cur.execute('INSERT INTO users (username,password_hash,is_admin) VALUES (?,?,1)',
                    ('228820', generate_password_hash('228820')))
        db.commit()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def log_action(user_id, action):
    db = get_db()
    db.execute('INSERT INTO audit_logs (user_id, action) VALUES (?,?)', (user_id, action))
    db.commit()


@app.before_request
def set_csp_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)


@app.after_request
def set_security_headers(response):
    # CSP using per-request nonce for inline scripts/styles and allowing TinyMCE CDN
    nonce = getattr(g, 'csp_nonce', '')
    csp = f"default-src 'self' https:; script-src 'self' 'nonce-{nonce}' https://cdn.tiny.cloud; style-src 'self' 'nonce-{nonce}' https:;"
    response.headers['Content-Security-Policy'] = csp
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = query_db('SELECT * FROM users WHERE id=?', (session['user_id'],), one=True)
        if not user or not user['is_admin']:
            return 'Forbidden', 403
        return f(*args, **kwargs)

    return decorated


@app.before_request
def setup():
    init_db()
    ensure_default_admin()


@app.route('/')
def index():
    if 'user_id' in session:
        user = query_db('SELECT * FROM users WHERE id=?', (session['user_id'],), one=True)
        if user and user['is_admin']:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username=?', (username,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('index'))
        flash('اسم مستخدم أو كلمة مرور خاطئة')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    # pagination and optional search
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    q = request.args.get('q')
    # advanced filters
    grade_f = request.args.get('grade')
    category_f = request.args.get('category')
    author_f = request.args.get('author')
    starred_f = request.args.get('starred')
    if q:
        users = query_db('SELECT * FROM users WHERE username LIKE ? ORDER BY id LIMIT ? OFFSET ?', (f'%{q}%', per_page, offset))
    else:
        users = query_db('SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?', (per_page, offset))
    contents = query_db('SELECT * FROM contents ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
    # apply filters in Python
    def content_matches(c):
        if grade_f and c['grades']:
            if str(grade_f) not in c['grades'].split(','):
                return False
        if category_f and c['categories']:
            if category_f not in [x.strip() for x in c['categories'].split(',')]:
                return False
        if author_f and str(c['author_id']) != str(author_f):
            return False
        if starred_f:
            # filter by author starred flag
            if starred_f == '1':
                # check if author is starred
                a = query_db('SELECT * FROM users WHERE id=?', (c['author_id'],), one=True)
                if not a or not a['starred']:
                    return False
        return True
    contents = [c for c in contents if content_matches(c)]
    return render_template('admin_dashboard.html', users=users, contents=contents, page=page)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        grade = int(request.form.get('grade') or 0)
        if password:
            pw = password
        else:
            try:
                plen = int(get_setting('password_length', '8'))
            except Exception:
                plen = 8
            pw = secrets.token_urlsafe(plen)[:plen]
        is_admin_flag = 1 if request.form.get('is_admin') == 'on' or request.form.get('role') == 'admin' else 0
        role = request.form.get('role') or 'user'
        db = get_db()
        db.execute('INSERT INTO users (username,password_hash,grade,is_admin,role) VALUES (?,?,?,?,?)',
                   (username, generate_password_hash(pw), grade, is_admin_flag, role))
        db.commit()
        flash('تم إضافة المستخدم')
        log_action(session['user_id'], f"added user:{username}")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_user.html')


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = query_db('SELECT * FROM users WHERE id=?', (user_id,), one=True)
    if not user:
        return 'Not found', 404
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password')
        grade = int(request.form.get('grade') or 0)
        starred = 1 if request.form.get('starred') == 'on' else 0
        db = get_db()
        is_admin_flag = 1 if request.form.get('is_admin') == 'on' or request.form.get('role') == 'admin' else 0
        role = request.form.get('role') or user.get('role', 'user')
        if password:
            db.execute('UPDATE users SET username=?, password_hash=?, grade=?, starred=?, is_admin=?, role=? WHERE id=?',
                       (username, generate_password_hash(password), grade, starred, is_admin_flag, role, user_id))
        else:
            db.execute('UPDATE users SET username=?, grade=?, starred=?, is_admin=?, role=? WHERE id=?',
                       (username, grade, starred, is_admin_flag, role, user_id))
        db.commit()
        flash('تم التحديث')
        log_action(session['user_id'], f"edited user:{username}")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit_user.html', user=user)


@app.route('/admin/contents/add', methods=['GET', 'POST'])
@admin_required
def admin_add_content():
    if request.method == 'POST':
        title = request.form.get('title')
        html = request.form.get('html')
        link = request.form.get('link')
        categories = request.form.get('categories')
        grades = ','.join(request.form.getlist('grades'))
        # handle upload
        upload_path = None
        if 'file' in request.files:
            f = request.files['file']
            url = save_upload_file(f)
            if url:
                link = link or url
        # sanitize HTML but allow basic tags
        allowed_tags = ['p','b','i','u','a','img','ul','ol','li','br','strong','em','h1','h2','h3','h4','iframe','div','span']
        allowed_attrs = {'a': ['href','target','rel'], 'img': ['src','alt','style'], 'iframe': ['src','width','height','frameborder','allow','allowfullscreen'], '*': ['style','class']}
        safe_html = bleach.clean(html or '', tags=allowed_tags, attributes=allowed_attrs, strip=True)
        db = get_db()
        db.execute('INSERT INTO contents (title,html,link,categories,grades,author_id) VALUES (?,?,?,?,?,?)',
                   (title, safe_html, link, categories, grades, session['user_id']))
        db.commit()
        flash('تم إضافة المحتوى')
        log_action(session['user_id'], f"added content:{title}")
        return redirect(url_for('admin_dashboard'))
    users = query_db('SELECT DISTINCT grade FROM users ORDER BY grade')
    return render_template('admin_add_content.html', users=users)


@app.route('/admin/contents/edit/<int:cid>', methods=['GET', 'POST'])
@admin_required
def admin_edit_content(cid):
    content = query_db('SELECT * FROM contents WHERE id=?', (cid,), one=True)
    if not content:
        return 'Not found', 404
    if request.method == 'POST':
        title = request.form.get('title')
        html = request.form.get('html')
        link = request.form.get('link')
        categories = request.form.get('categories')
        grades = ','.join(request.form.getlist('grades'))
        # handle upload
        if 'file' in request.files:
            f = request.files['file']
            url = save_upload_file(f)
            if url:
                link = link or url
        allowed_tags = ['p','b','i','u','a','img','ul','ol','li','br','strong','em','h1','h2','h3','h4','iframe','div','span']
        allowed_attrs = {'a': ['href','target','rel'], 'img': ['src','alt','style'], 'iframe': ['src','width','height','frameborder','allow','allowfullscreen'], '*': ['style','class']}
        safe_html = bleach.clean(html or '', tags=allowed_tags, attributes=allowed_attrs, strip=True)
        db = get_db()
        db.execute('UPDATE contents SET title=?,html=?,link=?,categories=?,grades=? WHERE id=?',
                   (title, safe_html, link, categories, grades, cid))
        db.commit()
        flash('تم التحديث')
        log_action(session['user_id'], f"edited content:{title}")
        return redirect(url_for('admin_dashboard'))
    users = query_db('SELECT DISTINCT grade FROM users ORDER BY grade')
    return render_template('admin_edit_content.html', content=content, users=users)


@app.route('/admin/preview')
@admin_required
def admin_preview():
    # preview all contents as a normal user would see them, with optional filters
    grade = request.args.get('grade')
    category = request.args.get('category')
    q = 'SELECT * FROM contents'
    rows = query_db(q)
    if grade:
        rows = [r for r in rows if (not r['grades']) or str(grade) in (r['grades'].split(','))]
    if category:
        rows = [r for r in rows if r['categories'] and category in r['categories'].split(',')]
    grades = query_db('SELECT DISTINCT grade FROM users ORDER BY grade')
    return render_template('admin_preview.html', contents=rows, grades=grades)


@app.route('/admin/export')
@admin_required
def admin_export():
    contents = query_db('SELECT * FROM contents ORDER BY id DESC')
    out = [dict(c) for c in contents]
    return jsonify(out)


@app.route('/admin/audit')
@admin_required
def admin_audit():
    logs = query_db('SELECT * FROM audit_logs ORDER BY ts DESC')
    return render_template('admin_audit.html', logs=logs)


@app.route('/admin/export/csv')
@admin_required
def admin_export_csv():
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','ts','user_id','action'])
    for l in query_db('SELECT * FROM audit_logs ORDER BY ts DESC'):
        writer.writerow([l['id'], l['ts'], l['user_id'], l['action']])
    return si.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="audit.csv"'}


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


def get_setting(key, default=None):
    r = query_db('SELECT value FROM settings WHERE key=?', (key,), one=True)
    return r['value'] if r else default


@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        pw_len = request.form.get('password_length') or '8'
        sanitize = '1' if request.form.get('sanitize') == 'on' else '0'
        db = get_db()
        db.execute('REPLACE INTO settings (key,value) VALUES (?,?)', ('password_length', str(pw_len)))
        db.execute('REPLACE INTO settings (key,value) VALUES (?,?)', ('sanitize_html', sanitize))
        db.commit()
        flash('تم حفظ الاعدادات')
        return redirect(url_for('admin_settings'))
    pw_len = get_setting('password_length', '8')
    sanitize = get_setting('sanitize_html', '1')
    return render_template('admin_settings.html', password_length=pw_len, sanitize=(sanitize=='1'))


@app.route('/admin/contents/import', methods=['GET', 'POST'])
@admin_required
def admin_import_contents():
    if request.method == 'POST':
        import json
        if 'jsonfile' not in request.files:
            flash('رجاء حدد ملف')
            return redirect(url_for('admin_import_contents'))
        f = request.files['jsonfile']
        if not f or not f.filename.endswith('.json'):
            flash('ملف غير صحيح')
            return redirect(url_for('admin_import_contents'))
        try:
            data = json.loads(f.read().decode('utf-8'))
            db = get_db()
            imported = 0
            if not isinstance(data, list):
                data = [data]
            for item in data:
                # check if exists by id (skip duplicates by default)
                if db.execute('SELECT id FROM contents WHERE id=?', (item.get('id'),)).fetchone():
                    continue
                title = item.get('title', '')
                html = item.get('html', '')
                link = item.get('link', '')
                categories = item.get('categories', '')
                grades = item.get('grades', '')
                safe_html = bleach.clean(html or '', tags=['p','b','i','u','a','img','ul','ol','li','br','strong','em','h1','h2','h3','h4','iframe','div','span'], attributes={'a': ['href','target','rel'], 'img': ['src','alt','style'], 'iframe': ['src','width','height','frameborder','allow','allowfullscreen'], '*': ['style','class']}, strip=True)
                db.execute('INSERT INTO contents (title,html,link,categories,grades,author_id) VALUES (?,?,?,?,?,?)',
                           (title, safe_html, link, categories, grades, session['user_id']))
                imported += 1
            db.commit()
            flash(f'تم استيراد {imported} محتوى')
            log_action(session['user_id'], f"imported {imported} contents from JSON")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f'خطأ: {str(e)}')
    return render_template('admin_import.html')


@app.route('/admin/contents/export/json')
@admin_required
def admin_export_contents_json():
    contents = query_db('SELECT * FROM contents ORDER BY id DESC')
    out = [dict(c) for c in contents]
    return jsonify(out)

@app.route('/user')
@login_required
def user_dashboard():
    user = query_db('SELECT * FROM users WHERE id=?', (session['user_id'],), one=True)
    all_contents = query_db('SELECT * FROM contents ORDER BY id DESC')
    visible = []
    for c in all_contents:
        if not c['grades']:
            visible.append(c)
        else:
            gstrs = c['grades'].split(',')
            if str(user['grade']) in gstrs:
                visible.append(c)
    categories = set()
    for c in visible:
        if c['categories']:
            categories.update([x.strip() for x in c['categories'].split(',') if x.strip()])
    # sidebar grades
    grades = sorted(set([r['grade'] for r in query_db('SELECT grade FROM users') if r['grade']]))
    return render_template('user_dashboard.html', contents=visible, categories=sorted(categories), grades=grades)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
