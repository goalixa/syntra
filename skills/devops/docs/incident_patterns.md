# Kubernetes Incident Patterns

This document defines common Kubernetes failure patterns and their remediation steps for the DevOpsAgent.

---

## Pattern 1: Pod Pending

**Symptom**: Pod stays in `Pending` state

**Common Causes**:
- Insufficient cluster resources (CPU/memory)
- No node matching pod affinity/anti-affinity rules
- PVC bound to unavailable PV
- Resource quota exceeded

**Investigation Steps**:
1. Check pod events: `kubectl describe pod <name> -n <namespace>`
2. Check node resources: `kubectl top nodes`
3. Check PVC status: `kubectl get pvc -n <namespace>`

**Remediation**:
- Scale down other workloads to free resources
- Add more nodes to the cluster
- Adjust pod affinity rules
- Delete unused PVCs

---

## Pattern 2: ImagePullBackOff

**Symptom**: Pod fails to pull container image

**Common Causes**:
- Invalid image name or tag
- Image not in registry
- Missing image pull secret
- Registry authentication failure

**Investigation Steps**:
1. Check pod events for specific error
2. Verify image exists in registry
3. Check image pull secrets

**Remediation**:
- Fix image name/tag in deployment
- Create image pull secret: `kubectl create secret docker-registry`
- Add secret to service account

---

## Pattern 3: CrashLoopBackOff

**Symptom**: Container restarts repeatedly

**Common Causes**:
- Application startup failure
- Missing environment variables/config
- Port already in use
- Out of memory (OOMKilled)
- Liveness/readiness probe failure

**Investigation Steps**:
1. Check container logs: `kubectl logs <pod> -n <namespace> --previous`
2. Check pod events for exit codes
3. Review resource limits

**Remediation**:
- Fix application configuration
- Increase memory limits
- Fix liveness/readiness probe configuration
- Fix application bugs causing crashes

---

## Pattern 4: OOMKilled

**Symptom**: Container terminated due to memory limit

**Common Causes**:
- Memory limit too low
- Memory leak in application
- Too many concurrent requests

**Investigation Steps**:
1. Check container logs for OOM messages
2. Review memory usage over time
3. Check for memory leaks in application

**Remediation**:
- Increase memory limits
- Fix memory leaks in application
- Implement caching to reduce memory usage

---

## Pattern 5: Evicted Pod

**Symptom**: Pod evicted from node

**Common Causes**:
- Node disk pressure
- Node memory pressure
- Node CPU pressure
- Node network unavailable

**Investigation Steps**:
1. Check node conditions: `kubectl describe node <node>`
2. Check for disk/memory pressure
3. Review eviction events

**Remediation**:
- Free disk space on node
- Add more nodes
- Reduce memory pressure
- Check for node issues

---

## Pattern 6: Unhealthy Readiness Probe

**Symptom**: Pod ready condition is False

**Common Causes**:
- Application not ready to serve traffic
- Readiness probe misconfigured
- Application startup taking too long

**Investigation Steps**:
1. Check pod status: `kubectl get pod -n <namespace>`
2. Review readiness probe configuration
3. Check application health endpoint

**Remediation**:
- Fix readiness probe configuration
- Increase initialDelaySeconds
- Fix application health check endpoint

---

## Pattern 7: Deployment Rollout Stuck

**Symptom**: Deployment doesn't progress

**Common Causes**:
- Image pull failure
- Container can't start
- Liveness probe failure
- Insufficient resources

**Investigation Steps**:
1. Check rollout status: `kubectl rollout status deployment/<name> -n <namespace>`
2. Check deployment events
3. Check pod status

**Remediation**:
- Check image availability
- Fix container configuration
- Adjust resource limits

---

## Pattern 8: Service Not Reaching Pod

**Symptom**: Service can't communicate with pods

**Common Causes**:
- Pod not ready (wrong label)
- Pod not in Service endpoints
- Network policy blocking
- DNS issues

**Investigation Steps**:
1. Check Service endpoints: `kubectl get endpoints <service> -n <namespace>`
2. Check pod labels match Service selector
3. Test DNS resolution

**Remediation**:
- Fix pod labels to match Service selector
- Fix network policy
- Fix DNS configuration

---

## Pattern 9: Ingress 502/504 Errors

**Symptom**: Ingress returns 502 or 504

**Common Causes**:
- No ready pods for service
- Pods not listening on expected port
- Service type mismatch
- Backend timeout

**Investigation Steps**:
1. Check Ingress events
2. Check Service endpoints
3. Test pod connectivity from Ingress pod

**Remediation**:
- Ensure pods are ready
- Verify service port configuration
- Increase backend timeout

---

## Pattern 10: PVC Pending

**Symptom**: PVC stuck in Pending state

**Common Causes**:
- No storage class available
- Storage quota exceeded
- Provisioner not working
- PVC misconfigured

**Investigation Steps**:
1. Check PVC events
2. Check StorageClass exists
3. Check storage provider

**Remediation**:
- Create required StorageClass
- Add storage capacity
- Fix PVC configuration
- Check provisioner health

---

## Quick Reference Commands

```bash
# Get pod status in namespace
kubectl get pods -n <namespace>

# Describe pod for events
kubectl describe pod <pod> -n <namespace>

# Get container logs
kubectl logs <pod> -n <namespace> --previous

# Check rollout status
kubectl rollout status deployment/<name> -n <namespace>

# Get service endpoints
kubectl get endpoints <service> -n <namespace>

# Check node resources
kubectl top nodes

# Check PVC status
kubectl get pvc -n <namespace>
```

---

## Emergency Response Flow

1. **Identify**: Get pod/deployment status
2. **Diagnose**: Use `kubectl describe` and logs
3. **Contain**: Scale down or delete problematic pods
4. **Fix**: Apply remediation
5. **Verify**: Confirm recovery
6. **Document**: Record incident details