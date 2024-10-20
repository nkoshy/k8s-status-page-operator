# Kubernetes Status Page Operator

## Overview

The Kubernetes Status Page Operator is a custom controller that automatically manages components on a status page (like StatusPage.io) based on the state of resources in your Kubernetes cluster. It allows you to monitor specific Pods, Services, and Ingresses across selected namespaces and reflect their status on your status page.

## Features

- Automatically create, update, and delete status page components based on Kubernetes resources
- Selectively monitor specific resources using CustomResourceDefinitions (CRDs)
- Configure monitored namespaces using a ConfigMap
- Real-time status updates based on Kubernetes events
- Easy integration with StatusPage.io (extensible to other status page providers)

## Prerequisites

- Kubernetes cluster (version 1.16+)
- `kubectl` configured to communicate with your cluster
- Docker (for building the operator image)
- StatusPage.io account (or similar status page service)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/k8s-status-page-operator.git
   cd k8s-status-page-operator
   ```

2. Build the Docker image:
   ```
   docker build -t your-registry/statuspage-operator:latest .
   docker push your-registry/statuspage-operator:latest
   ```

3. Create a Secret with your StatusPage API key and page ID:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: statuspage-secrets
     namespace: default
   type: Opaque
   stringData:
     api-key: your-statuspage-api-key
     page-id: your-statuspage-page-id
   ```
   Apply this Secret to your cluster:
   ```
   kubectl apply -f statuspage-secrets.yaml
   ```

4. Apply the Kubernetes resources:
   ```
   kubectl apply -f crd.yaml
   kubectl apply -f configmap.yaml
   kubectl apply -f rbac.yaml
   kubectl apply -f deployment.yaml
   ```

## Configuration

### Monitored Namespaces

Edit the `statuspage-operator-config` ConfigMap to specify which namespaces should be monitored:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: statuspage-operator-config
  namespace: default
data:
  config.yaml: |
    monitored_namespaces:
      - default
      - production
      - staging
```

Apply the changes:
```
kubectl apply -f configmap.yaml
```

The operator will automatically reload the configuration every 5 minutes.

## Usage

To monitor a specific Kubernetes resource:

1. Create a `StatusPageMonitor` custom resource:

   ```yaml
   apiVersion: statuspage.example.com/v1
   kind: StatusPageMonitor
   metadata:
     name: monitor-my-service
     namespace: default
   spec:
     resourceType: Service
     resourceName: my-service
     namespace: default
   ```

2. Apply the custom resource:
   ```
   kubectl apply -f status-page-monitor.yaml
   ```

The operator will create a corresponding component on your status page and keep it updated based on the state of the Kubernetes resource.

## Development

### Prerequisites

- Python 3.9+
- pipenv

### Setting up the development environment

1. Install dependencies:
   ```
   pipenv install
   ```

2. Activate the virtual environment:
   ```
   pipenv shell
   ```

3. Run the operator locally:
   ```
   kopf run status_page_operator.py --verbose
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.