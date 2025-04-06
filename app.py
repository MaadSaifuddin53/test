import os
from flask import Flask, redirect, url_for, session, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

# ---------------- GitHub OAuth ----------------
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = 'http://localhost:5000/callback/github'
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com/user"

# ---------------- Zoom OAuth ----------------
ZOOM_CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.getenv('ZOOM_CLIENT_SECRET')
ZOOM_REDIRECT_URI = 'http://localhost:5000/callback/zoom'
ZOOM_AUTH_URL = "https://zoom.us/oauth/authorize"
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE_URL = "https://api.zoom.us/v2"

# ---------------- GitHub Routes ----------------
@app.route('/')
def home():
    return '''
    <h2>Login</h2>
    <a href="/login/github">Login with GitHub</a><br>
    <a href="/login/zoom">Login with Zoom</a>
    '''

@app.route('/login/github')
def login_github():
    github_auth_url = f"{GITHUB_AUTH_URL}?client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_REDIRECT_URI}&scope=user"
    return redirect(github_auth_url)

@app.route('/callback/github')
def callback_github():
    code = request.args.get('code')
    if not code:
        return "Error: no code received from GitHub", 400

    response = requests.post(
        GITHUB_TOKEN_URL,
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': GITHUB_REDIRECT_URI
        },
        headers={'Accept': 'application/json'}
    )

    token_data = response.json()
    if 'access_token' in token_data:
        session['github_access_token'] = token_data['access_token']
        return redirect(url_for('profile_github'))
    return "Error getting GitHub access token", 400

@app.route('/profile/github')
def profile_github():
    if 'github_access_token' not in session:
        return redirect(url_for('login_github'))

    headers = {
        'Authorization': f"Bearer {session['github_access_token']}"
    }
    response = requests.get(GITHUB_API_URL, headers=headers)
    return jsonify(response.json())

# ---------------- Zoom Routes ----------------
@app.route('/login/zoom')
def login_zoom():
    zoom_auth_url = f"{ZOOM_AUTH_URL}?response_type=code&client_id={ZOOM_CLIENT_ID}&redirect_uri={ZOOM_REDIRECT_URI}"
    return redirect(zoom_auth_url)

@app.route('/callback/zoom')
def callback_zoom():
    code = request.args.get('code')
    if not code:
        return "Error: no code received from Zoom", 400

    auth = (ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': ZOOM_REDIRECT_URI
    }

    response = requests.post(ZOOM_TOKEN_URL, auth=auth, data=data)
    token_data = response.json()

    if 'access_token' in token_data:
        session['zoom_access_token'] = token_data['access_token']
        session['zoom_user_id'] = token_data.get('user_id')  # optional
        return redirect(url_for('zoom_profile'))
    return "Error getting Zoom access token", 400

@app.route('/zoom/profile')
def zoom_profile():
    if 'zoom_access_token' not in session:
        return redirect(url_for('login_zoom'))

    headers = {
        'Authorization': f"Bearer {session['zoom_access_token']}"
    }

    response = requests.get(f"{ZOOM_API_BASE_URL}/users/me", headers=headers)
    return jsonify(response.json())

@app.route('/zoom/create_meeting')
def create_zoom_meeting():
    if 'zoom_access_token' not in session:
        return redirect(url_for('login_zoom'))

    headers = {
        'Authorization': f"Bearer {session['zoom_access_token']}",
        'Content-Type': 'application/json'
    }

    data = {
        "topic": "Flask OAuth Test Meeting",
        "type": 1  # Instant meeting
    }

    response = requests.post(f"{ZOOM_API_BASE_URL}/users/me/meetings", headers=headers, json=data)
    return jsonify(response.json())

@app.route('/zoom/list_meetings')
def list_zoom_meetings():
    if 'zoom_access_token' not in session:
        return redirect(url_for('login_zoom'))

    headers = {
        'Authorization': f"Bearer {session['zoom_access_token']}"
    }

    response = requests.get(f"{ZOOM_API_BASE_URL}/users/me/meetings", headers=headers)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)
