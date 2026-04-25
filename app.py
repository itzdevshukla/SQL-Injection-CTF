from flask import Flask, request, jsonify, send_from_directory, redirect, make_response
import sqlite3
import secrets
import os

app = Flask(__name__, static_folder='.')
PORT = 8000
DB_FILE = "users.db"

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    # Add a dummy admin user if not exists
    c.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'SuperSecretPassword123')")
    conn.commit()
    conn.close()

# Simple Key-Value Session Store (In-Memory)
# In production, use Redis or a proper session interface.
SESSIONS = set()

def create_session():
    session_id = secrets.token_hex(16)
    SESSIONS.add(session_id)
    return session_id

def is_authenticated(request):
    session_token = request.cookies.get('session_token')
    return session_token in SESSIONS

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Protect specific files
    if filename in ['dashboard.html', 'secrets.html']:
        if not is_authenticated(request):
            return redirect('/')
    return send_from_directory('.', filename)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # VULNERABLE QUERY: String concatenation allowing SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"Executing Query: {query}") 
    
    try:
        c.execute(query)
        user = c.fetchone()
        
        if user:
            session_id = create_session()
            response = make_response(jsonify({'status': 'success', 'message': 'Login successful', 'redirect': '/dashboard.html'}))
            response.set_cookie('session_token', session_id, httponly=True)
            return response
        else:
            return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    # For local testing
    app.run(host='0.0.0.0', port=PORT, debug=True)
else:
    # When running with Gunicorn, just init the DB
    init_db()
