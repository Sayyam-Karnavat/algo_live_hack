from flask import Flask, render_template, request, redirect, flash
import sqlite3, os, pickle, hashlib
from werkzeug.utils import secure_filename
from generate_account import generate_account

app = Flask(__name__)
app.secret_key = "your_flask_secret_key"  # Used only for flashing messages

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔧 Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY NOT NULL,
    password TEXT NOT NULL,
    image BLOB,
    wallet_address TEXT,
    private_key TEXT,
    mnemonic TEXT,
    pickle_transaction BLOB,
    signature_count INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

# 🔐 Hash password using SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 🔍 Check if username already exists
def user_id_exists(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['username']  # still coming from 'username' input
        raw_password = request.form['password']
        image = request.files['profileImage']

        if user_id_exists(user_id):
            flash("⚠️ User ID already exists. Please choose another.")
            return redirect('/')

        hashed_password = hash_password(raw_password)
        image_blob = image.read() if image else None

        mnemonic_phrase, private_key, wallet_address = generate_account()

        dummy_tx = {"from": wallet_address, "to": "some_wallet", "amount": 100}
        pickled_tx = pickle.dumps(dummy_tx)

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (user_id, password, image, wallet_address, private_key, mnemonic, pickle_transaction, signature_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, hashed_password, image_blob, wallet_address, private_key, mnemonic_phrase, pickled_tx, 0))
        conn.commit()
        conn.close()

        flash("✅ User registered successfully!")
        return redirect('/')

    return render_template('register.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
