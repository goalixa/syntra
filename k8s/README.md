# Syntra Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Syntra AI Orchestrator service.

## Prerequisites

1. Kubernetes cluster with NGINX Ingress Controller
2. cert-manager installed (for TLS certificates)
3. kubectl configured to access your cluster

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Deploy Application

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### 3. Update Image

After GitHub Actions builds and pushes a new image:

```bash
# Using latest tag
kubectl set image deployment/syntra syntra=ghcr.io/YOUR_USERNAME/syntra:latest -n syntra

# Or with specific tag
kubectl set image deployment/syntra syntra=ghcr.io/YOUR_USERNAME/syntra:TAG -n syntra

# Watch the rollout
kubectl rollout status deployment/syntra -n syntra
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n syntra

# Check service
kubectl get svc -n syntra

# Check ingress
kubectl get ingress -n syntra

# View logs
kubectl logs -f deployment/syntra -n syntra
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_SERVICE_URL` | `http://auth-service.goalixa-auth.svc.cluster.local` | Auth service URL |
| `KUBECTL_PATH` | `/usr/bin/kubectl` | Path to kubectl binary |
| `MODEL_NAME` | `claude` | AI model to use |

Update these in `deployment.yaml` as needed.

### Resources

Default resource limits:
- CPU: 100m - 500m
- Memory: 256Mi - 512Mi

Adjust in `deployment.yaml` based on your needs.

### Ingress

The Ingress is configured for:
- **Host**: `syntra.goalixa.com`
- **TLS**: Enabled with Let's Encrypt (cert-manager)

Update the host in `ingress.yaml` to match your domain.

## Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment/syntra --replicas=3 -n syntra
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete namespace only
kubectl delete namespace syntra
```

## Troubleshooting

```bash
# Check pod status
kubectl describe pod -l app=syntra -n syntra

# View logs
kubectl logs -f deployment/syntra -n syntra

# Port forward for local testing
kubectl port-forward -n syntra deployment/syntra 8000:80

# Exec into pod
kubectl exec -it -n syntra deployment/syntra -- /bin/bash
```
