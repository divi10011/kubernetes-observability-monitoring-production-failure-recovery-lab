# High memory
**Symptoms:** HighMemoryUsage alert, OOM risk. **Investigate:** `kubectl top pods -n monitoring-lab`; inspect application logs. **Resolve:** fix retention/leaks or increase the justified limit. **Validate:** working-set memory trends down. **Prevent:** memory profiling and limits.
