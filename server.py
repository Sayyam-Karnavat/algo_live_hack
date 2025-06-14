import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"
from flask import Flask, render_template, request, redirect, flash, send_file
import sqlite3, os, pickle, hashlib
import cv2
import numpy as np
from generate_account import generate_account
from arc19 import ARC19  # Assuming ARC19 is available in your project
import base64
import io
import requests
import tensorflow as tf

app = Flask(__name__)
app.secret_key = "ssk"

UPLOAD_FOLDER = 'static/uploads'
TEMP_UPLOAD_FOLDER = 'temp_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_UPLOAD_FOLDER'] = TEMP_UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)

# AI Model Constants
MODEL_PATH = "face_recognition.keras"
IMAGE_SHAPE = (224, 224, 3)
CLASS_NAMES = ["John", "Grace", "Lily", "Michelle", "Sebastin"]
CONFIDENCE_THRESHOLD = 0.99
CLASS_NAME_MAPS = {
    "John": "john",
    "Grace": "grace",
    "Lily": "lily",
    "Michelle": "michelle",
    "Sebastin": "sebastin"
}

# Load AI model at startup
os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"
try:
    MODEL = tf.keras.models.load_model(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    MODEL = None

def load_and_preprocess_image(image_path):
    """Load and preprocess an image for inference."""
    try:
        img = tf.io.read_file(image_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, [IMAGE_SHAPE[0], IMAGE_SHAPE[1]])
        img = img / 255.0
        img = tf.expand_dims(img, axis=0)
        return img
    except Exception as e:
        raise Exception(f"Error loading image {image_path}: {str(e)}")

def predict_employee(image_path):
    """Predict employee name from an image."""
    if MODEL is None:
        raise Exception("AI model not loaded.")
    try:
        img = load_and_preprocess_image(image_path)
        predictions = MODEL.predict(img, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = predictions[0][predicted_class]
        if confidence >= CONFIDENCE_THRESHOLD:
            predicted_employee = CLASS_NAMES[predicted_class]
        else:
            predicted_employee = "unknown"
        return predicted_employee, confidence * 100
    except Exception as e:
        raise Exception(f"Error during prediction: {str(e)}")

# 🔧 Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY NOT NULL,
            password TEXT NOT NULL,
            encrypted_image BLOB,
            original_image BLOB,
            wallet_address TEXT,
            private_key TEXT,
            mnemonic TEXT,
            pickle_transaction BLOB,
            signature_count INTEGER DEFAULT 0,
            salt TEXT,
            transaction_id TEXT,
            cid TEXT,
            ipfs_link TEXT,
            asset_id TEXT
        )
    ''')
    conn.commit()
    c.execute('''
        CREATE TABLE IF NOT EXISTS blacklisted_data( 
            blacklisted_waddress TEXT PRIMARY KEY NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_to_blacklist(wallet_address):
    """Insert a given wallet address into the blacklisted_data table."""
    if not wallet_address:
        print("⚠️ Invalid wallet address provided.")
        return
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO blacklisted_data (blacklisted_waddress) VALUES (?)", (wallet_address,))
        conn.commit()
        conn.close()
        print(f"✅ Wallet address {wallet_address} has been added to the blacklist.")
    except sqlite3.Error as e:
        print(f"⚠️ Failed to insert into blacklist: {e}")



# 🔐 Hash password using SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 🔐 Generate integer key from password and salt
def derive_key(password, salt):
    salted_password = password.encode() + base64.b64decode(salt)
    hash_obj = hashlib.sha256(salted_password)
    key = int.from_bytes(hash_obj.digest()[:4], byteorder='big')
    return key

# 🔐 Generate key matrix for XOR encryption
def generate_key_matrix(shape, key):
    """Generate a key matrix for XOR encryption using a seed."""
    np.random.seed(key)
    return np.random.randint(0, 256, size=shape, dtype=np.uint8)

# 🔐 Encrypt image
def encrypt_image(image, key):
    """Encrypt the image using XOR with a key-based matrix."""
    key_matrix = generate_key_matrix(image.shape, key)
    encrypted = cv2.bitwise_xor(image, key_matrix)
    return encrypted

# 🔐 Decrypt image
def decrypt_image(encrypted_image, key):
    """Decrypt the image using XOR with the same key-based matrix."""
    key_matrix = generate_key_matrix(encrypted_image.shape, key)
    decrypted = cv2.bitwise_xor(encrypted_image, key_matrix)
    return decrypted

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
        user_id = request.form['username']
        raw_password = request.form['password']
        image = request.files['profileImage']

        if user_id_exists(user_id):
            flash("⚠️ User ID already exists. Please choose another.")
            return redirect('/')

        hashed_password = hash_password(raw_password)
        
        salt_bytes = os.urandom(16)
        salt = base64.b64encode(salt_bytes).decode('utf-8')
        
        encrypted_image_blob = None
        original_image_blob = None
        cid = None
        transaction_id = None
        temp_image_path = None
        if image:
            image_data = image.read()
            if not image_data:
                flash("⚠️ Invalid or empty image file.")
                return redirect('/')
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                flash("⚠️ Failed to process image. Ensure it’s a valid image file.")
                return redirect('/')
            key = derive_key(raw_password, salt)
            encrypted_img = encrypt_image(img, key)
            _, encrypted_buffer = cv2.imencode('.jpg', encrypted_img)
            encrypted_image_blob = encrypted_buffer.tobytes()
            original_image_blob = image_data

            temp_image_path = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], f"{user_id}_temp.jpg")
            cv2.imwrite(temp_image_path, encrypted_img)

            try:
                arc_obj = ARC19()
                cid = arc_obj.upload_metadata(file_path=temp_image_path)
                metadata_hash, nft_url = arc_obj.create_metadata(
                    asset_name=user_id,
                    description="Encrypted profile image NFT",
                    ipfs_hash=cid
                )
                reserve_address = arc_obj.reserve_address_from_cid(cid=cid)
                url = arc_obj.create_url_from_cid(cid=cid)
                transaction_id , asset_ID = arc_obj.create_asset(
                    metadata_hash=metadata_hash,
                    reserve_address=reserve_address,
                    url=url
                )
            except Exception as e:
                flash(f"⚠️ NFT minting failed: {str(e)}")
                if temp_image_path and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                return redirect('/')
            finally:
                if temp_image_path and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)

        mnemonic_phrase, private_key, wallet_address = generate_account()

        dummy_tx = {"from": wallet_address, "to": "some_wallet", "amount": 100}
        pickled_tx = pickle.dumps(dummy_tx)

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (user_id, password, encrypted_image, original_image, wallet_address, private_key, mnemonic, pickle_transaction, signature_count, salt, transaction_id, cid, ipfs_link , asset_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, hashed_password, encrypted_image_blob, original_image_blob, wallet_address, private_key, mnemonic_phrase, pickled_tx, 0, salt, transaction_id, cid, nft_url , asset_ID))
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            flash(f"⚠️ Database error: {str(e)}")
            return redirect('/')
        finally:
            conn.close()

        flash("✅ User registered successfully!")
        return redirect('/')

    return render_template('register.html')

@app.route('/decrypt_image', methods=['GET', 'POST'])
def decrypt_image():
    if request.method == 'GET':
        return render_template('decrypt.html')

    user_id = request.form['user_id']
    password = request.form['password']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT ipfs_link, salt FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        flash("⚠️ User ID not found.")
        return redirect('/decrypt_image')

    ipfs_link, salt = result
    if not ipfs_link:
        flash("⚠️ No IPFS link found for this user.")
        return redirect('/decrypt_image')

    try:
        response = requests.get(ipfs_link, timeout=10)
        if response.status_code != 200:
            flash(f"⚠️ Failed to download image from IPFS: HTTP {response.status_code}")
            return redirect('/decrypt_image')
        
        nparr = np.frombuffer(response.content, np.uint8)
        encrypted_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if encrypted_img is None:
            flash("⚠️ Failed to process downloaded image.")
            return redirect('/decrypt_image')
        
        key = derive_key(password, salt)
        decrypted_img = decrypt_image(encrypted_img, key)
        
        _, buffer = cv2.imencode('.jpg', decrypted_img)
        decrypted_image_bytes = buffer.tobytes()
        
        return send_file(
            io.BytesIO(decrypted_image_bytes),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f'{user_id}_profile.jpg'
        )
    except requests.RequestException as e:
        flash(f"⚠️ Failed to download image from IPFS: {str(e)}")
        return redirect('/decrypt_image')
    except Exception as e:
        flash(f"⚠️ Decryption failed: {str(e)}")
        return redirect('/decrypt_image')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    password = request.form['password']
    image = request.files['employeeImage']


    if not image:
        flash("⚠️ Please upload an image.")
        return redirect('/login')

    # Save image temporarily for AI prediction
    temp_image_path = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], f"login_temp_{hashlib.md5(os.urandom(16)).hexdigest()}.jpg")
    try:
        image.save(temp_image_path)
        if not os.path.exists(temp_image_path):
            flash("⚠️ Failed to process image. Try again.")
            return redirect('/login')

        

        # Run AI prediction
        predicted_employee, confidence = predict_employee(temp_image_path)

        print(predicted_employee)
        print(password)


        if predicted_employee == "unknown":
            flash("⚠️ User not identified by AI.")
            return redirect('/login')

        # Map predicted employee to user_id
        user_id = CLASS_NAME_MAPS.get(predicted_employee)
        if not user_id:
            flash("⚠️ User not identified by AI.")
            return redirect('/login')

        # Verify user_id and password in database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()

        
        if not result:
            flash("⚠️ Invalid credentials.")
            return redirect('/login')

        stored_hashed_password = result[0]
        input_hashed_password = hash_password(password)


        
        if stored_hashed_password == input_hashed_password:
            flash(f"✅ Login successful! Welcome, {user_id}.")
            return redirect('/login')
        else:
            flash("⚠️ Invalid credentials.")
            return redirect('/login')

    except Exception as e:
        flash(f"⚠️ Login failed: {str(e)}")
        return redirect('/login')
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=3333, debug=False)