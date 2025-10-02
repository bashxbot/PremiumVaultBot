
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='admin-panel/dist', static_url_path='')
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())

PLATFORMS = ['netflix', 'crunchyroll', 'spotify', 'wwe']
CREDENTIALS_DIR = 'credentials'
KEYS_FILE = 'bot/data/keys.json'
USERS_FILE = 'bot/data/users.json'
ADMIN_CREDS_FILE = 'admin_credentials.json'

def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return [] if 'keys' in filename or 'credentials' in filename or filename.endswith('.json') and 'users' not in filename else {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def ensure_credentials_dir():
    os.makedirs(CREDENTIALS_DIR, exist_ok=True)
    for platform in PLATFORMS:
        filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
        if not os.path.exists(filepath):
            save_json(filepath, [])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    admin_creds = load_json(ADMIN_CREDS_FILE)
    
    # Check owner credentials
    if admin_creds.get('owner', {}).get('username') == username and admin_creds.get('owner', {}).get('password') == password:
        session['logged_in'] = True
        session['username'] = username
        session['role'] = 'owner'
        return jsonify({'success': True, 'role': 'owner'})
    
    # Check admin credentials
    for admin in admin_creds.get('admins', []):
        if admin.get('username') == username and admin.get('password') == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'admin'
            return jsonify({'success': True, 'role': 'admin'})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'logged_in' in session:
        return jsonify({'authenticated': True, 'role': session.get('role', 'admin'), 'username': session.get('username')})
    return jsonify({'authenticated': False})

@app.route('/api/admins', methods=['GET'])
@login_required
def get_admins():
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Only owner can view admins'}), 403
    
    admin_creds = load_json(ADMIN_CREDS_FILE)
    admins = admin_creds.get('admins', [])
    # Don't send passwords
    safe_admins = [{'username': a['username']} for a in admins]
    return jsonify({'success': True, 'admins': safe_admins})

@app.route('/api/admins', methods=['POST'])
@login_required
def add_admin():
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Only owner can add admins'}), 403
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    admin_creds = load_json(ADMIN_CREDS_FILE)
    
    # Check if username already exists
    if admin_creds.get('owner', {}).get('username') == username:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    for admin in admin_creds.get('admins', []):
        if admin.get('username') == username:
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    admin_creds['admins'].append({'username': username, 'password': password, 'role': 'admin'})
    save_json(ADMIN_CREDS_FILE, admin_creds)
    
    return jsonify({'success': True, 'message': 'Admin added successfully'})

@app.route('/api/admins/<username>', methods=['DELETE'])
@login_required
def delete_admin(username):
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Only owner can delete admins'}), 403
    
    admin_creds = load_json(ADMIN_CREDS_FILE)
    admins = admin_creds.get('admins', [])
    
    admin_creds['admins'] = [a for a in admins if a['username'] != username]
    save_json(ADMIN_CREDS_FILE, admin_creds)
    
    return jsonify({'success': True, 'message': 'Admin deleted successfully'})

@app.route('/api/stats')
@login_required
def get_stats():
    ensure_credentials_dir()
    stats = {}
    for platform in PLATFORMS:
        filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
        creds = load_json(filepath)
        stats[platform] = {
            'total': len(creds),
            'active': len([c for c in creds if c.get('status') == 'active']),
            'claimed': len([c for c in creds if c.get('status') == 'claimed']),
            'inactive': len([c for c in creds if c.get('status') == 'inactive'])
        }
    
    keys_data = load_json(KEYS_FILE) if os.path.exists(KEYS_FILE) else []
    total_keys = len(keys_data)
    active_keys = len([k for k in keys_data if k.get('status') == 'active'])
    
    return jsonify({
        'platforms': PLATFORMS,
        'stats': stats,
        'total_keys': total_keys,
        'active_keys': active_keys
    })

@app.route('/api/credentials/<platform>', methods=['GET'])
@login_required
def get_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    return jsonify({'success': True, 'credentials': credentials})

@app.route('/api/credentials/<platform>', methods=['POST'])
@login_required
def add_credential(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    status = data.get('status', 'active')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    
    credentials.append({
        'email': email,
        'password': password,
        'status': status,
        'created_at': datetime.now().isoformat()
    })
    
    save_json(filepath, credentials)
    return jsonify({'success': True, 'message': 'Credential added successfully'})

@app.route('/api/credentials/<platform>/upload', methods=['POST'])
@login_required
def upload_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    
    content = file.read().decode('utf-8')
    lines = content.strip().split('\n')
    
    added_count = 0
    skipped_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split(':')
        if len(parts) >= 2:
            email = parts[0].strip()
            password = parts[1].strip()
            status = parts[2].strip() if len(parts) >= 3 else 'active'
            
            if email and password and '@' in email:
                credentials.append({
                    'email': email,
                    'password': password,
                    'status': status,
                    'created_at': datetime.now().isoformat()
                })
                added_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1
    
    save_json(filepath, credentials)
    message = f'Successfully added {added_count} credentials'
    if skipped_count > 0:
        message += f' ({skipped_count} skipped due to invalid format)'
    
    return jsonify({'success': True, 'message': message, 'added': added_count, 'skipped': skipped_count})

@app.route('/api/credentials/<platform>/<int:index>', methods=['DELETE'])
@login_required
def delete_credential(platform, index):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    
    if 0 <= index < len(credentials):
        credentials.pop(index)
        save_json(filepath, credentials)
        return jsonify({'success': True, 'message': 'Credential deleted successfully'})
    
    return jsonify({'success': False, 'message': 'Invalid index'}), 400

@app.route('/api/credentials/<platform>/<int:index>', methods=['PUT'])
@login_required
def edit_credential(platform, index):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    
    if 0 <= index < len(credentials):
        data = request.json
        email = data.get('email')
        password = data.get('password')
        status = data.get('status')
        
        if email:
            credentials[index]['email'] = email
        if password:
            credentials[index]['password'] = password
        if status:
            credentials[index]['status'] = status
        
        credentials[index]['updated_at'] = datetime.now().isoformat()
        save_json(filepath, credentials)
        return jsonify({'success': True, 'message': 'Credential updated successfully'})
    
    return jsonify({'success': False, 'message': 'Invalid index'}), 400

@app.route('/api/keys/<platform>', methods=['GET'])
@login_required
def get_keys(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    keys_data = load_json(KEYS_FILE) if os.path.exists(KEYS_FILE) else []
    users_data = load_json(USERS_FILE) if os.path.exists(USERS_FILE) else {}
    
    if not isinstance(users_data, dict):
        users_data = {}
    
    platform_keys = [k for k in keys_data if k.get('platform', '').lower() == platform.lower()]
    
    for key in platform_keys:
        key['users_info'] = []
        if 'used_by' in key:
            for user_id in key['used_by']:
                user_id_str = str(user_id)
                if user_id_str in users_data:
                    user_info = users_data[user_id_str]
                    if isinstance(user_info, dict):
                        key['users_info'].append({
                            'id': user_id,
                            'joined': user_info.get('joined_at', 'N/A')
                        })
    
    return jsonify({'success': True, 'keys': platform_keys})

if __name__ == '__main__':
    ensure_credentials_dir()
    app.run(host='0.0.0.0', port=5000, debug=True)
