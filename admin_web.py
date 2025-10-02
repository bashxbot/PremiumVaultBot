from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())

PLATFORMS = ['netflix', 'crunchyroll', 'spotify', 'wwe']
CREDENTIALS_DIR = 'credentials'
KEYS_FILE = 'data/keys.json'
USERS_FILE = 'data/users.json'

def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return []

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def ensure_credentials_dir():
    os.makedirs(CREDENTIALS_DIR, exist_ok=True)
    for platform in PLATFORMS:
        filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
        if not os.path.exists(filepath):
            save_json(filepath, [])

@app.route('/')
def index():
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
    
    return render_template('index.html', stats=stats, platforms=PLATFORMS, total_keys=total_keys, active_keys=active_keys)

@app.route('/credentials/<platform>')
def view_credentials(platform):
    if platform not in PLATFORMS:
        flash('Invalid platform', 'error')
        return redirect(url_for('index'))
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    return render_template('credentials.html', platform=platform, credentials=credentials)

@app.route('/credentials/<platform>/add', methods=['POST'])
def add_credential(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    email = request.form.get('email')
    password = request.form.get('password')
    status = request.form.get('status', 'active')
    
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

@app.route('/credentials/<platform>/upload', methods=['POST'])
def upload_credentials(platform):
    if platform not in PLATFORMS:
        flash('Invalid platform', 'error')
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('view_credentials', platform=platform))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('view_credentials', platform=platform))
    
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
    flash(message, 'success')
    return redirect(url_for('view_credentials', platform=platform))

@app.route('/credentials/<platform>/delete/<int:index>', methods=['POST'])
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

@app.route('/credentials/<platform>/edit/<int:index>', methods=['POST'])
def edit_credential(platform, index):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    filepath = os.path.join(CREDENTIALS_DIR, f'{platform}.json')
    credentials = load_json(filepath)
    
    if 0 <= index < len(credentials):
        email = request.form.get('email')
        password = request.form.get('password')
        status = request.form.get('status')
        
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

@app.route('/keys')
def view_keys():
    keys_data = load_json(KEYS_FILE) if os.path.exists(KEYS_FILE) else []
    users_data = load_json(USERS_FILE) if os.path.exists(USERS_FILE) else {}
    
    if not isinstance(users_data, dict):
        users_data = {}
    
    for key in keys_data:
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
    
    return render_template('keys.html', keys=keys_data)

if __name__ == '__main__':
    ensure_credentials_dir()
    app.run(host='0.0.0.0', port=5000, debug=True)
