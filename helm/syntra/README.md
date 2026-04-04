# Syntra Helm Chart

This Helm chart deploys the Syntra AI Orchestrator service on Kubernetes.

## Prerequisites

- Kubernetes cluster (version 1.19+)
- Helm 3.x installed
- NGINX Ingress Controller (for Ingress)
- cert-manager (for TLS certificates, optional)

## Installation

### 1. Update values.yaml

Edit `helm/syntra/values.yaml` and update:
- `image.repository`: Your GitHub Container Registry path (e.g., `ghcr.io/yourusername/syntra`)
- `ingress.hosts`: Your domain name

### 2. Install the Chart

```bash
# From the helm directory
helm install syntra ./syntra --namespace syntra --create-namespace

# Or from the project root
helm install syntra ./helm/syntra --namespace syntra --create-namespace
```

### 3. Upgrade the Chart

```bash
# After building a new image
helm upgrade syntra ./helm/syntra --namespace syntra \
  --set image.tag=latest
```

## Configuration

The following table lists the configurable parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Docker image repository | `ghcr.io/YOUR_USERNAME/syntra` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `image.tag` | Docker image tag | `latest` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `80` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Ingress host | `syntra.goalixa.com` |
| `ingress.tls[0].secretName` | TLS secret name | `syntra-tls` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `256Mi` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `namespace` | Kubernetes namespace | `syntra` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_SERVICE_URL` | `http://auth.goalixa-auth.svc.cluster.local` | Auth service URL |
| `KUBECTL_PATH` | `/usr/bin/kubectl` | Path to kubectl binary |
| `MODEL_NAME` | `claude` | AI model to use |

## Deploy with Specific Image Tag

```bash
# Deploy with specific tag
helm install syntra ./helm/syntra --namespace syntra --create-namespace \
  --set image.tag=v1.0.0

# Upgrade with specific tag
helm upgrade syntra ./helm/syntra --namespace syntra \
  --set image.tag=v1.0.0
```

## Uninstall

```bash
helm uninstall syntra --namespace syntra
```

## Scaling

```bash
# Scale using Helm
helm upgrade syntra ./helm/syntra --namespace syntra \
  --set replicaCount=3

# Or enable autoscaling
helm upgrade syntra ./helm/syntra --namespace syntra \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=1 \
  --set autoscaling.maxReplicas=5
```

## Troubleshooting

```bash
# Check deployment status
helm status syntra --namespace syntra

# View Helm values
helm get values syntra --namespace syntra

# View all manifests
helm get manifest syntra --namespace syntra

# Check pods
kubectl get pods -n syntra

# View logs
kubectl logs -f -n syntra -l app.kubernetes.io/name=syntra

# Port forward for local testing
kubectl port-forward -n syntra deployment/syntra 8000:80
```

## Custom Values File

Create a `my-values.yaml` file:

```yaml
image:
  repository: ghcr.io/myusername/syntra
  tag: "v1.0.0"

ingress:
  hosts:
    - host: syntra.mydomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: syntra-custom-tls
      hosts:
        - syntra.mydomain.com

replicaCount: 2

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 200m
    memory: 512Mi
```

Install with custom values:

```bash
helm install syntra ./helm/syntra --namespace syntra --create-namespace -f my-values.yaml
```
