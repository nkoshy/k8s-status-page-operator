import kopf
import kubernetes
import os
import requests
import yaml

# Configure Kubernetes API client
kubernetes.config.load_incluster_config()
api = kubernetes.client.CustomObjectsApi()
core_v1_api = kubernetes.client.CoreV1Api()

# StatusPage API configuration
STATUS_PAGE_API_KEY = os.environ.get('STATUS_PAGE_API_KEY')
STATUS_PAGE_PAGE_ID = os.environ.get('STATUS_PAGE_PAGE_ID')
STATUS_PAGE_API_BASE = 'https://api.statuspage.io/v1'

# Load configuration from ConfigMap
def load_config():
    config_map = core_v1_api.read_namespaced_config_map('statuspage-operator-config', 'default')
    return yaml.safe_load(config_map.data['config.yaml'])

config = load_config()

@kopf.on.create('statuspage.example.com', 'v1', 'statuspagemonitors')
def create_status_component(body, spec, meta, **kwargs):
    resource_type = spec['resourceType']
    resource_name = spec['resourceName']
    namespace = spec['namespace']

    if namespace not in config['monitored_namespaces']:
        raise kopf.PermanentError(f"Namespace {namespace} is not in the list of monitored namespaces")

    # Create component via StatusPage API
    url = f"{STATUS_PAGE_API_BASE}/pages/{STATUS_PAGE_PAGE_ID}/components"
    headers = {
        'Authorization': f'OAuth {STATUS_PAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'component': {
            'name': f"{resource_type}: {namespace}/{resource_name}",
            'description': f"Kubernetes {resource_type} in namespace {namespace}",
            'status': 'operational'
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        component_id = response.json()['id']
        return {'status': 'created', 'id': component_id}
    else:
        raise kopf.PermanentError(f"Failed to create component: {response.text}")

@kopf.on.delete('statuspage.example.com', 'v1', 'statuspagemonitors')
def delete_status_component(body, meta, spec, status, **kwargs):
    component_id = status['create_fn']['id']

    # Delete component via StatusPage API
    url = f"{STATUS_PAGE_API_BASE}/pages/{STATUS_PAGE_PAGE_ID}/components/{component_id}"
    headers = {
        'Authorization': f'OAuth {STATUS_PAGE_API_KEY}'
    }
    
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        return {'status': 'deleted'}
    else:
        raise kopf.PermanentError(f"Failed to delete component: {response.text}")

@kopf.on.event('', 'v1', 'pods')
@kopf.on.event('', 'v1', 'services')
@kopf.on.event('networking.k8s.io', 'v1', 'ingresses')
def update_component_status(body, meta, spec, status, **kwargs):
    namespace = meta['namespace']
    name = meta['name']
    kind = body['kind']

    if namespace not in config['monitored_namespaces']:
        return

    # Check if this resource is being monitored
    monitors = api.list_namespaced_custom_object(
        group="statuspage.example.com",
        version="v1",
        namespace=namespace,
        plural="statuspagemonitors",
    )
    
    monitored = any(
        m['spec']['resourceType'] == kind and
        m['spec']['resourceName'] == name and
        m['spec']['namespace'] == namespace
        for m in monitors['items']
    )

    if not monitored:
        return

    # Determine status (this is a simplified example)
    if kind == 'Pod':
        component_status = 'operational' if status.get('phase') == 'Running' else 'partial_outage'
    elif kind == 'Service':
        component_status = 'operational'  # You might want to check endpoints here
    elif kind == 'Ingress':
        component_status = 'operational'  # You might want to check the Ingress status

    # Update component status
    # You'd need to store and retrieve the component ID for the monitored resource
    # This is a simplified example
    component_id = "YOUR_COMPONENT_ID"  # You need to implement a way to store and retrieve this
    url = f"{STATUS_PAGE_API_BASE}/pages/{STATUS_PAGE_PAGE_ID}/components/{component_id}"
    headers = {
        'Authorization': f'OAuth {STATUS_PAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'component': {
            'status': component_status
        }
    }
    
    requests.patch(url, json=data, headers=headers)

# Periodically reload the config
@kopf.timer('', interval=300.0)
def reload_config(**kwargs):
    global config
    config = load_config()
    print(f"Reloaded config: {config}")