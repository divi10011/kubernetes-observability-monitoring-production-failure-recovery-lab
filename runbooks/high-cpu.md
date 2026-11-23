# High CPU
**Symptoms:** HighCPUUsage alert or HPA growth. **Investigate:** `kubectl top pods -n monitoring-lab`; query CPU in Grafana. **Resolve:** stop excess traffic, optimize work, or tune requests/HPA. **Validate:** utilisation falls and replicas stabilise. **Prevent:** capacity tests and efficient endpoints.
