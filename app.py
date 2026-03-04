from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import random
import string
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "meghalaya_secret_key_2024"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'applications.db'

EMAIL_ADDRESS = "sangmagam35@gmail.com"
EMAIL_PASSWORD = "fozz cvwx nzcy vrqm"

TWILIO_ACCOUNT_SID = "USd4fabee6325fb9cb1b8f3e8bf2513d99"
TWILIO_AUTH_TOKEN = "G22XCT4XBPVSFAPTWX5RB3FV"
TWILIO_PHONE_NUMBER = "+917630022159"

def ensure_folders():
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
        print("Created uploads folder")

def init_db():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS applications
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT, email TEXT, phone TEXT,
                      photo_path TEXT, submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS verification_codes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      application_id INTEGER, code TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      expires_at TIMESTAMP, verified INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database error: {e}")

ensure_folders()
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    return ''.join(random.choices(string.digits, k=5))

def send_email(email, code):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = 'Meghalaya Job - Verification Code'
        body = f"Your verification code is: {code}. Valid for 60 seconds."
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_sms(phone, code):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your Meghalaya Job verification code is: {code}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"✅ SMS sent to {phone}")
        return True
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Index error: {e}")
        return "Error loading page", 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(photo_path)
                print(f"Photo saved: {photo_path}")
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO applications (name, email, phone, photo_path) VALUES (?, ?, ?, ?)", 
                  (name, email, phone, photo_path))
        conn.commit()
        app_id = c.lastrowid
        conn.close()
        print(f"Application saved with ID: {app_id}")
        
        code = generate_code()
        expires_at = datetime.now() + timedelta(seconds=60)
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO verification_codes (application_id, code, expires_at) VALUES (?, ?, ?)", 
                  (app_id, code, expires_at))
        conn.commit()
        conn.close()
        print(f"Verification code generated: {code}")
        
        send_email(email, code)
        send_sms(phone, code)
        
        session['application_id'] = app_id
        session['verification_code'] = code
        
        return redirect(url_for('verify'))
        
    except Exception as e:
        print(f"Submit error: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    try:
        if 'verification_code' not in session:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            user_code = request.form['verification_code']
            if user_code == session['verification_code']:
                session.pop('verification_code', None)
                return redirect(url_for('success'))
            else:
                flash('Incorrect verification code. Please try again.', 'error')
        
        return render_template('verify.html')
        
    except Exception as e:
        print(f"Verify error: {e}")
        return redirect(url_for('index'))

@app.route('/success')
def success():
    try:
        return render_template('success.html')
    except Exception as e:
        print(f"Success error: {e}")
        return "Error loading page", 500

@app.route('/admin')
def admin():
    try:
        password = request.args.get('password')
        if password != 'admin123':
            return "Access Denied. Please use the correct password.", 403
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM applications ORDER BY submitted_at DESC")
        rows = c.fetchall()
        conn.close()
        
        return render_template('admin.html', applications=rows)
        
    except Exception as e:
        print(f"Admin error: {e}")
        return "Error loading admin page", 500

@app.route('/delete_single', methods=['POST'])
def delete_single():
    try:
        data = request.get_json()
        app_id = data.get('id')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute("SELECT photo_path FROM applications WHERE id = ?", (app_id,))
        result = c.fetchone()
        if result and result[0]:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], result[0])
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        c.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Delete single error: {e}")
        return jsonify({'success': False}), 500

@app.route('/delete_selected', methods=['POST'])
def delete_selected():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        for app_id in ids:
            c.execute("SELECT photo_path FROM applications WHERE id = ?", (app_id,))
            result = c.fetchone()
            if result and result[0]:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], result[0])
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except:
                        pass
            c.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'deleted_count': len(ids)})
        
    except Exception as e:
        print(f"Delete selected error: {e}")
        return jsonify({'success': False}), 500

if __name__ == '__main__':
    print("Starting server...")
    print(f"Email configured: {EMAIL_ADDRESS}")
    print(f"SMS configured: {TWILIO_PHONE_NUMBER}")
    app.run(debug=True, host='0.0.0.0', port=5000)