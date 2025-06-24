import os
import sqlite3
from flask import Flask, send_from_directory, render_template, request, url_for, jsonify, redirect, flash, session, get_flashed_messages # ADDED get_flashed_messages
from flask_socketio import SocketIO
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("No SECRET_KEY set for Flask application. Please set it in a .env file or as an environment variable.")

socketio = SocketIO(app)

# Create the 'uploads' directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Establish a connection to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database and create tables if they don't exist
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER, content TEXT, media_url TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_contacts
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 adder_id INTEGER NOT NULL,
                 contact_id INTEGER NOT NULL,
                 added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 UNIQUE(adder_id, contact_id),
                 FOREIGN KEY(adder_id) REFERENCES users(id),
                 FOREIGN KEY(contact_id) REFERENCES users(id))''')
    conn.commit()

# --- Login Required Decorator (Defined only ONCE) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function
# --- End Login Required Decorator ---


@app.route('/')
def registration_page():
    # If a user is already logged in, redirect them to their messages
    if 'user_id' in session:
        return redirect(url_for('view_messages', user_id=session['user_id']))
    return render_template('start.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    with get_db_connection() as conn:
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            return jsonify({'status': 'danger', 'message': 'Email already exists. Please choose another or login.'}), 409
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_password))
        conn.commit()
    return jsonify({'status': 'success', 'message': 'Registration successful! Redirecting to login...'})

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    # If a user is already logged in, redirect them to their messages
    if 'user_id' in session:
        return redirect(url_for('view_messages', user_id=session['user_id']))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash('Login successful!', 'success')
                return jsonify({'status': 'success', 'message': 'Login successful! Redirecting...', 'user_id': user['id']})
            return jsonify({'status': 'danger', 'message': 'Invalid email or password.'}), 401
    return render_template("login.html")

@app.route('/logout')
@login_required # This is actually fine here, as explained above.
def logout():
    session.pop('user_id', None) # Remove user_id from session
    session.pop('user_name', None) # Remove user_name from session (if stored)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_page'))

@app.route('/add_contact/<int:user_id>', methods=['GET'])
@login_required # Apply decorator
def add_contact_page(user_id):
    # CRITICAL: Prevent logged-in users from accessing another user's add contact page
    if user_id != session.get('user_id'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('view_messages', user_id=session.get('user_id')))
    return render_template('add_contact.html', user_id=user_id)

@app.route('/add_contact', methods=['POST'])
@login_required # Apply decorator
def add_contact():
    adder_id = request.form.get('adder_id')
    
    # CRITICAL: Verify that the adder_id from the form matches the logged-in user's ID
    if int(adder_id) != session.get('user_id'):
        return jsonify({'status': 'danger', 'message': 'Unauthorized action.'}), 403

    contact_email = request.form.get('contact_email')

    if not adder_id or not contact_email:
        return jsonify({'status': 'danger', 'message': 'Missing adder ID or contact email.'}), 400

    try:
        adder_id = int(adder_id)
    except ValueError:
        return jsonify({'status': 'danger', 'message': 'Invalid adder ID.'}), 400

    with get_db_connection() as conn:
        contact_user = conn.execute('SELECT id, email FROM users WHERE email = ?', (contact_email,)).fetchone()

        if not contact_user:
            return jsonify({'status': 'danger', 'message': f'User with email "{contact_email}" not found.'}), 404

        contact_id = contact_user['id']

        existing_contact = conn.execute(
            'SELECT * FROM user_contacts WHERE adder_id = ? AND contact_id = ?',
            (adder_id, contact_id)
        ).fetchone()

        if existing_contact:
            return jsonify({'status': 'warning', 'message': f'"{contact_email}" is already in your contacts.'}), 409

        try:
            conn.execute(
                'INSERT INTO user_contacts (adder_id, contact_id) VALUES (?, ?)',
                (adder_id, contact_id)
            )
            conn.commit()
            return jsonify({'status': 'success', 'message': f'"{contact_email}" added to your contacts successfully!'}), 200
        except sqlite3.IntegrityError:
            return jsonify({'status': 'danger', 'message': 'Database error: Contact already exists or constraint violation.'}), 500
        except Exception as e:
            return jsonify({'status': 'danger', 'message': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/get_user_contacts/<int:user_id>', methods=['GET'])
@login_required # Apply decorator
def get_user_contacts(user_id):
    # CRITICAL: Prevent logged-in users from fetching another user's contacts
    if user_id != session.get('user_id'):
        return jsonify([]), 403 # Return empty list and Forbidden status
    
    with get_db_connection() as conn:
        contacts = conn.execute('''
            SELECT u.id, u.email
            FROM user_contacts uc
            JOIN users u ON uc.contact_id = u.id
            WHERE uc.adder_id = ?
        ''', (user_id,)).fetchall()
    return jsonify([{'id': contact['id'], 'email': contact['email']} for contact in contacts])


@app.route('/send_message/<int:sender_id>', methods=['GET'])
@login_required # Apply decorator
def send_message_with_id(sender_id):
    # CRITICAL: Prevent logged-in users from accessing another user's send page
    if sender_id != session.get('user_id'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('view_messages', user_id=session.get('user_id')))
    return render_template('send.html', sender_id=sender_id)

@app.route('/send', methods=['POST'])
@login_required # Apply decorator
def send_message():
    sender_id = request.form.get('sender_id')
    
    # CRITICAL: Verify that the sender_id from the form matches the logged-in user's ID
    if int(sender_id) != session.get('user_id'):
        return jsonify({'status': 'danger', 'message': 'Unauthorized action.'}), 403

    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content')
    media_url = None

    if not sender_id or not receiver_id:
        return jsonify({'status': 'danger', 'message': 'Sender or receiver ID missing.'}), 400
    if not content and 'file' not in request.files:
        return jsonify({'status': 'danger', 'message': 'Message content or a file is required to send a message.'}), 400

    # Convert IDs to int
    try:
        sender_id = int(sender_id)
        receiver_id = int(receiver_id)
    except ValueError:
        return jsonify({'status': 'danger', 'message': 'Invalid sender or receiver ID format.'}), 400

    # Check if a file was uploaded
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            upload_dir = 'uploads'
            media_url = os.path.join(upload_dir, filename)
            try:
                file.save(media_url)
            except Exception as e:
                return jsonify({'status': 'danger', 'message': f'Error saving file: {str(e)}'}), 500

    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO messages (sender_id, receiver_id, content, media_url) VALUES (?, ?, ?, ?)',
                         (sender_id, receiver_id, content, media_url))
            conn.commit()
    except Exception as e:
        return jsonify({'status': 'danger', 'message': f'Error saving message to database: {str(e)}'}), 500

    return jsonify({'status': 'success', 'message': 'Message sent successfully!'})

@app.route('/uploads/<path:filename>', methods=['GET'])
@login_required # Protect access to uploaded files
def uploaded_file(filename):
    # OPTIONAL: You might want to add more specific logic here to ensure
    # the logged-in user is authorized to view THIS specific file (e.g.,
    # they are the sender, receiver, or part of a group chat).
    return send_from_directory('uploads', filename)

@app.route('/api/messages/<int:user_id>', methods=['GET'])
@login_required # Apply decorator
def get_messages_api(user_id):
    # CRITICAL: Prevent logged-in users from fetching another user's messages
    if user_id != session.get('user_id'):
        return jsonify([]), 403 # Return empty list and Forbidden status
    
    with get_db_connection() as conn:
        messages = conn.execute('''
            SELECT m.id, m.content, m.media_url, m.timestamp,
                   s.name AS sender_name, s.email AS sender_email,
                   r.name AS receiver_name, r.email AS receiver_email
            FROM messages AS m
            JOIN users AS s ON m.sender_id = s.id
            JOIN users AS r ON m.receiver_id = r.id
            WHERE m.receiver_id = ? OR m.sender_id = ?
            ORDER BY m.timestamp ASC
        ''', (user_id, user_id)).fetchall()
    
    messages_data = []
    for msg in messages:
        msg_dict = dict(msg)
        if msg_dict['timestamp']:
            try:
                dt_obj = datetime.strptime(msg_dict['timestamp'], '%Y-%m-%d %H:%M:%S')
                msg_dict['timestamp'] = dt_obj.isoformat() + 'Z'
            except ValueError:
                msg_dict['timestamp'] = msg_dict['timestamp']
        messages_data.append(msg_dict)
    
    return jsonify(messages_data)

@app.route('/messages/<int:user_id>', methods=['GET'])
@login_required # Apply decorator
def view_messages(user_id):
    # CRITICAL: Prevent logged-in users from viewing another user's messages page
    if user_id != session.get('user_id'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('view_messages', user_id=session.get('user_id'))) # Redirect to their own messages
    
    with get_db_connection() as conn:
        user = conn.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            # This case implies a user_id that doesn't exist, even if logged in.
            # It's good to clear the session and redirect to login.
            session.pop('user_id', None)
            session.pop('user_name', None)
            flash('User not found or session invalid. Please log in again.', 'danger')
            return redirect(url_for('login_page'))
        user_name = user['name']
    
    return render_template('messages.html', user_id=user_id, user_name=user_name)

@app.route('/users', methods=['GET'])
@login_required # Apply decorator (protect if you don't want public access to user list)
def get_all_users():
    # This route is less sensitive if it only shows email/ID, but if it's for internal use, protect it.
    with get_db_connection() as conn:
        users = conn.execute('SELECT id, email FROM users').fetchall()
    return jsonify([{'id': user['id'], 'email': user['email']} for user in users])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
