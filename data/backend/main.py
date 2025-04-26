from flask import Flask, jsonify
import docker
import os
from datetime import datetime
from dotenv import load_dotenv
import re

load_dotenv()
DEBUG = os.getenv('DOCKERCONTAINERMANAGER_DEBUG')

app = Flask(__name__)

client = docker.DockerClient(base_url='unix://var/run/docker.sock')

def convert_ansi_to_html(text):
    ansi_colors = {
        '30': 'ansi-black',
        '31': 'ansi-red',
        '32': 'ansi-green',
        '33': 'ansi-yellow',
        '34': 'ansi-blue',
        '35': 'ansi-magenta',
        '36': 'ansi-cyan',
        '37': 'ansi-white',
        '90': 'ansi-bright-black',
        '91': 'ansi-bright-red',
        '92': 'ansi-bright-green',
        '93': 'ansi-bright-yellow',
        '94': 'ansi-bright-blue',
        '95': 'ansi-bright-magenta',
        '96': 'ansi-bright-cyan',
        '97': 'ansi-bright-white',
        '1': 'ansi-bold',
        '2': 'ansi-dim',
        '3': 'ansi-italic',
        '4': 'ansi-underline',
        '5': 'ansi-blink',
        '0': 'ansi-reset'
    }
    
    pattern = r'\x1b\[([0-9;]*)m'
    
    def replace_ansi(match):
        codes = match.group(1).split(';')
        classes = []
        for code in codes:
            if code in ansi_colors:
                classes.append(ansi_colors[code])
        return f'<span class="{" ".join(classes)}">' if classes else '</span>'
    
    html = re.sub(pattern, replace_ansi, text)
    html = html.replace('\x1b[m', '</span>')
    html = html.replace('\x1b[K', '')
    html = html.replace('>....', '')
    html = re.sub(r'\x1b\[\?[0-9]+[hl]', '', html)
    html = re.sub(r'\x1b\[[0-9]+[hl]', '', html)
    html = re.sub(r'\x1b\[[0-9]+[A-Z]', '', html)
    html = re.sub(r'\x1b\[[0-9]+[a-z]', '', html)
    html = re.sub(r'</span>\s*<span[^>]*>', '', html)
    html = re.sub(r'<span[^>]*>\s*</span>', '', html)
    html = re.sub(r'<span[^>]*>\s*</span>', '', html)
    html = re.sub(r'</span>\s*$', '', html)
    html = re.sub(r'^\s*<span[^>]*>', '', html)
    html = re.sub(r'</span>\s*<span[^>]*>', '', html)
    html = re.sub(
        r'(\[\d{2}:\d{2}:\d{2}\] \[[^\]]+\/INFO\] \[minecraft\/[^\]]+\]:[^\n]+)',
        r'<span class="ansi-green">\1</span>',
        html
    )
    
    return html

@app.route('/api/containers')
def get_containers():
    try:
        containers = client.containers.list(all=True, filters={"label": "gamecontainermanager.enable=true"})
        
        if not containers:
            return jsonify([])
        
        containers_data = []
        for container in containers:
            container_status = container.status
            started_at = container.attrs['State']['StartedAt'] if container_status == 'running' else None

            if container.labels.get('gamecontainermanager.group'):
                label = container.labels['gamecontainermanager.group']
            elif container.labels.get('com.docker.compose.project'):
                label = container.labels['com.docker.compose.project']
            else:
                label = 'Groupe non défini'

            custom_labels = []
            for i in range(10):
                label_key = f'gamecontainermanager.customlabel{i}'
                if container.labels.get(label_key):
                    custom_labels.append(container.labels[label_key])
            
            has_custom_labels = len(custom_labels) > 0

            container_info = {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'is_running': container.status == 'running',
                'started_at': started_at,
                'group': label,
                'custom_labels': custom_labels,
                'has_custom_labels': has_custom_labels
            }
            
            containers_data.append(container_info)
        
        return jsonify(containers_data)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/container/<container_id>/restart', methods=['POST'])
def restart_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.restart()
        
        return jsonify({
            'status': 'success',
            'message': f'Container {container_id} restarted successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/container/<container_id>/stop', methods=['POST'])
def stop_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.stop()
        
        return jsonify({
            'status': 'success',
            'message': f'Container {container_id} stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
@app.route('/api/container/<container_id>/start', methods=['POST'])
def start_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.start()
        
        return jsonify({
            'status': 'success',
            'message': f'Container {container_id} started successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/group/<group_name>/start', methods=['POST'])
def start_group(group_name):
    try:
        containers = client.containers.list(
            all=True,
            filters={
                "label": [
                    "gamecontainermanager.enable=true",
                    f"gamecontainermanager.group={group_name}"
                ]
            }
        )
        
        for container in containers:
            if container.status != 'running':
                container.start()
        
        return jsonify({
            'status': 'success',
            'message': f'All containers in group {group_name} started successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/group/<group_name>/restart', methods=['POST'])
def restart_group(group_name):
    try:
        containers = client.containers.list(
            all=True,
            filters={
                "label": [
                    "gamecontainermanager.enable=true",
                    f"gamecontainermanager.group={group_name}"
                ]
            }
        )
        
        for container in containers:
            container.restart()
        
        return jsonify({
            'status': 'success',
            'message': f'All containers in group {group_name} restarted successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/group/<group_name>/stop', methods=['POST'])
def stop_group(group_name):
    try:
        containers = client.containers.list(
            all=True,
            filters={
                "label": [
                    "gamecontainermanager.enable=true",
                    f"gamecontainermanager.group={group_name}"
                ]
            }
        )
        
        for container in containers:
            if container.status == 'running':
                container.stop()
        
        return jsonify({
            'status': 'success',
            'message': f'All containers in group {group_name} stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/container/<container_id>/logs')
def get_container_logs(container_id):
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=100, timestamps=True).decode('utf-8')
        html_logs = convert_ansi_to_html(logs)
        return jsonify({
            'status': 'success',
            'logs': html_logs
        })
    except docker.errors.NotFound:
        return jsonify({
            'status': 'error',
            'message': 'Container not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=DEBUG) 