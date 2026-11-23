# Optional Splunk HEC integration

Create a dedicated non-production index such as `paytrack_lab`, then create an HEC
token restricted to that index. Never use an employer or production Splunk endpoint.

Create the local cluster Secret without writing its token to a file:

```powershell
kubectl -n monitoring-lab create secret generic splunk-hec `
  --from-literal=SPLUNK_HEC_HOST='your-splunk-host.example.com' `
  --from-literal=SPLUNK_HEC_PORT='8088' `
  --from-literal=SPLUNK_HEC_TOKEN='replace-me' `
  --from-literal=SPLUNK_INDEX='paytrack_lab'
```

Install Fluent Bit only when a safe test HEC endpoint exists. The supplied values
file reads every connection value from that Secret.

Useful searches:

```spl
index=paytrack_lab namespace_name=monitoring-lab
index=paytrack_lab "payment_accepted"
index=paytrack_lab "request_failed" OR status_code>=500
index=paytrack_lab kubernetes.pod_name="paytrack-*"
```
