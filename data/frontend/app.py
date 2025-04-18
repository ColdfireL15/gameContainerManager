from flask import Flask, render_template, flash, redirect, url_for
import requests
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv('DOCKERCONTAINERMANAGER_DEBUG')

app = Flask(__name__)

BACKEND_URL = os.getenv('DOCKERCONTAINERMANAGER_BACKEND_URL', 'http://backend:5000')

@app.route('/')
def index():
    try:
        response = requests.get(f"{BACKEND_URL}/api/containers")
        containers = response.json()
        return render_template('index.html', containers=containers)
    except Exception as e:
        print("Erreur:", str(e))
        return render_template('index.html', error=str(e))

@app.route('/api/container/<container_id>/stop', methods=['POST'])
def stop_container(container_id):
    try:
        response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/stop")
        return response.json()

    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/restart', methods=['POST'])
def restart_container(container_id):
    try:
        response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/restart")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/start', methods=['POST'])
def start_container(container_id):
    try:
        response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/start")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/group/<group_name>/start', methods=['POST'])
def start_group(group_name):
    try:
        response = requests.post(f"{BACKEND_URL}/api/group/{group_name}/start")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/group/<group_name>/restart', methods=['POST'])
def restart_group(group_name):
    try:
        response = requests.post(f"{BACKEND_URL}/api/group/{group_name}/restart")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/group/<group_name>/stop', methods=['POST'])
def stop_group(group_name):
    try:
        response = requests.post(f"{BACKEND_URL}/api/group/{group_name}/stop")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/container/<container_id>/logs')
def get_container_logs(container_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/container/{container_id}/logs")
        return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG) 