from flask import Flask, jsonify
import docker
from datetime import datetime

app = Flask(__name__)

client = docker.DockerClient(base_url='unix://var/run/docker.sock')

@app.route('/api/containers')
def get_containers():
    try:
        containers = client.containers.list(all=True, filters={"label": "docker-monitor.enable=true"})
        
        if not containers:
            return jsonify([])
        
        containers_data = []
        for container in containers:
            container_status = container.status
            started_at = container.attrs['State']['StartedAt'] if container_status == 'running' else None

            if container.labels.get('docker-monitor.group'):
                label = container.labels['docker-monitor.group']
            else:
                label = 'NoGroup'
            
            containers_data.append({
                'name': container.name,
                'id': container.id,
                'status': container_status,
                'is_running': container_status == 'running',
                'started_at': started_at,
                'group': label
            })
        
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
                    "docker-monitor.enable=true",
                    f"docker-monitor.group={group_name}"
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
                    "docker-monitor.enable=true",
                    f"docker-monitor.group={group_name}"
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
                    "docker-monitor.enable=true",
                    f"docker-monitor.group={group_name}"
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
        return jsonify({
            'status': 'success',
            'logs': logs
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
    app.run(host='0.0.0.0', port=5001) 