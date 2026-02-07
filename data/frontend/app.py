from flask import Flask, render_template, flash, redirect, url_for, session, request
import requests
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta
from wakeonlan import send_magic_packet

load_dotenv()
DEBUG = os.getenv('DOCKERCONTAINERMANAGER_DEBUG')

app = Flask(__name__)
app.secret_key = os.getenv('DOCKERCONTAINERMANAGER_SECRET_KEY')
if not app.secret_key:
    raise ValueError("PAS DE CLE SECRETE. Veuillez ajouter DOCKERCONTAINERMANAGER_SECRET_KEY dans votre .env")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

oauth = OAuth(app)
discord = oauth.register(
    name='discord',
    client_id=os.getenv('DOCKERCONTAINERMANAGER_DISCORD_CLIENT_ID'),
    client_secret=os.getenv('DOCKERCONTAINERMANAGER_DISCORD_CLIENT_SECRET'),
    authorize_url='https://discord.com/api/oauth2/authorize',
    authorize_params=None,
    access_token_url='https://discord.com/api/oauth2/token',
    access_token_params=None,
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify email'},
)

BACKEND_URL = os.getenv('DOCKERCONTAINERMANAGER_BACKEND_URL')
FRONTEND_URL = os.getenv('DOCKERCONTAINERMANAGER_FRONTEND_URL')
AUTHENTICATION = os.getenv('DOCKERCONTAINERMANAGER_AUTHENTICATION')
FAVICON_URL = os.getenv('DOCKERCONTAINERMANAGER_FAVICON_URL')
BACKEND_MAC_ADDR = os.getenv('DOCKERCONTAINERMANAGER_BACKEND_MAC_ADDR')
WOL_BOOT_UP_TIMER = int(os.getenv('WOL_BOOT_UP_TIMER', 30))

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login')
def login():
    if AUTHENTICATION == 'True':
        print("Le login est requis tant que la variable d'environnement DOCKERCONTAINERMANAGER_AUTHENTICATION est à True")
        return render_template('login.html', favicon_url=FAVICON_URL)
    else:
        return redirect(url_for('index'))

@app.route('/auth/discord')
def discord_auth():
    if AUTHENTICATION == 'True':
        redirect_uri = f"{FRONTEND_URL}/auth/discord/callback"
        return discord.authorize_redirect(redirect_uri)
    else:
        return redirect(url_for('index'))

@app.route('/auth/discord/callback')
def discord_callback():
    if AUTHENTICATION == 'True':
        token = discord.authorize_access_token()
        resp = discord.get('users/@me')
        user = resp.json()
    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'email': user.get('email', ''),
        'avatar': f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else None
    }
    session.permanent = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if AUTHENTICATION == 'True':
        session.pop('user', None)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('index'))

@app.route('/')
def index():
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    wol_available = bool(BACKEND_MAC_ADDR)
    try:
        response = requests.get(f"{BACKEND_URL}/api/containers", timeout=5)
        containers = response.json()
        return render_template('index.html', containers=containers, favicon_url=FAVICON_URL, wol_available=wol_available, wol_timer=WOL_BOOT_UP_TIMER)
    except Exception as e:
        print(f"Erreur lors de la récupération des conteneurs: {str(e)}")
        return render_template('index.html', error=str(e), favicon_url=FAVICON_URL, wol_available=wol_available, wol_timer=WOL_BOOT_UP_TIMER)

@app.route('/api/wol', methods=['POST'])
def wake_on_lan():
    if not BACKEND_MAC_ADDR:
        return {'status': 'error', 'message': 'Adresse MAC non configurée'}, 400
    try:
        send_magic_packet(BACKEND_MAC_ADDR)
        print(f"Magic packet WOL envoyé à {BACKEND_MAC_ADDR}")
        return {'status': 'success', 'message': f'Magic packet envoyé à {BACKEND_MAC_ADDR}'}
    except Exception as e:
        print(f"Erreur lors de l'envoi du WOL: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/stop', methods=['POST'])
def stop_container(container_id):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/stop")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/restart', methods=['POST'])
def restart_container(container_id):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/restart")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/start', methods=['POST'])
def start_container(container_id):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/start")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/group/<group_name>/start', methods=['POST'])
def start_group(group_name):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.post(f"{BACKEND_URL}/api/group/{group_name}/start")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/group/<group_name>/restart', methods=['POST'])
def restart_group(group_name):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.post(f"{BACKEND_URL}/api/group/{group_name}/restart")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/group/<group_name>/stop', methods=['POST'])
def stop_group(group_name):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.post(f"{BACKEND_URL}/api/group/{group_name}/stop")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/logs')
def get_container_logs(container_id):
    if AUTHENTICATION == 'True' and 'user' not in session:
        return redirect(url_for('login'))
    try:
        response = requests.get(f"{BACKEND_URL}/api/container/{container_id}/logs")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG) 