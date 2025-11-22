from flask import Flask, render_template, request, redirect, url_for
import sqlite3, os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    # جدول پست‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        filename TEXT,
        date_created TEXT NOT NULL,
        views INTEGER DEFAULT 0,
        pinned INTEGER DEFAULT 0
    )
    ''')

    # دسته‌بندی‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # اتصال پست‌ها به دسته‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS post_categories (
        post_id INTEGER,
        category_id INTEGER,
        FOREIGN KEY(post_id) REFERENCES posts(id),
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    ''')

    # کامنت‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        date_created TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )
    ''')

    # لایک‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_ip TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )
    ''')

    # ادمین‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # ساخت اولین ادمین (اگر نبود)
    admin_exists = conn.execute("SELECT * FROM admin_users").fetchone()
    if not admin_exists:
        conn.execute("INSERT INTO admin_users (username, password) VALUES (?, ?)",
                     ("admin", "admin123"))

    conn.commit()
    conn.close()

# ----------------- ROUTES -----------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('blog.html', posts=posts)

@app.route('/post/<int:post_id>')
def single_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()
    conn.close()
    if not post:
        return "Post not found", 404
    return render_template('post.html', post=post)

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        file = request.files.get('media')
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO posts (title, content, filename, date_created)
            VALUES (?, ?, ?, ?)
        ''', (title, content, filename, datetime.now()))
        conn.commit()
        conn.close()

        return redirect(url_for('blog'))

    return render_template('new_post.html', post=None)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()

    if not post:
        conn.close()
        return "Post not found", 404

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        file = request.files.get('media')
        filename = post['filename']

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn.execute('''
            UPDATE posts
            SET title=?, content=?, filename=?
            WHERE id=?
        ''', (title, content, filename, post_id))
        conn.commit()
        conn.close()

        return redirect(url_for('blog'))

    conn.close()
    return render_template('new_post.html', post=post)

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()

    if post:
        # حذف فایل واقعی
        if post['filename']:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], post['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)

        conn.execute('DELETE FROM posts WHERE id=?', (post_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('blog'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
