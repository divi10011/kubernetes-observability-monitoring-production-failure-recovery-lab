# ImagePullBackOff
**Symptoms:** pod stays Pending or ImagePullBackOff. **Investigate:** `kubectl describe pod -n monitoring-lab POD` and inspect Events for tag, registry, or credential failure. **Resolve:** correct the image reference or imagePullSecret, then restart the workload. **Validate:** `kubectl get pods -n monitoring-lab`. **Prevent:** immutable tags/digests and CI image checks.
