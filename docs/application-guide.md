# PayTrack application guide

## Purpose

PayTrack is a deliberately simulated payment API for learning Kubernetes operations.
It does not connect to payment processors and must never receive real customer data.
Payment records live only in a pod's memory, so they disappear when a pod restarts;
this is intentional for the observability and recovery lab.

## How it works

FastAPI serves HTTP requests through Uvicorn. Middleware measures each request and
writes a JSON completion event to stdout. Prometheus scrapes `/metrics` through the
Kubernetes ServiceMonitor. Kubernetes probes `/health` for liveness and `/ready`
for traffic eligibility. Two Deployment replicas sit behind the `paytrack` Service.

## Endpoints and example output

| Endpoint | Purpose | Example |
|---|---|---|
| `GET /` | Service identity | `{"service":"paytrack","environment":"kubernetes"}` |
| `GET /health` | Liveness probe | `{"status":"healthy"}` |
| `GET /ready` | Readiness probe | `{"status":"ready"}` |
| `GET /payments` | List simulated records | `{"items":[],"count":0}` |
| `POST /payments` | Create simulated record | HTTP `201`, status `accepted` |
| `GET /metrics` | Prometheus exposition | `paytrack_http_requests_total ...` |

Example request:

```powershell
Invoke-RestMethod http://localhost:8000/payments -Method POST -ContentType application/json -Body '{"amount":42.5,"currency":"INR","reference":"demo-order-001"}'
```

Example response:

```json
{"id":"<uuid>","amount":42.5,"currency":"INR","reference":"demo-order-001","status":"accepted"}
```

## Metrics and logs

PayTrack emits `paytrack_http_requests_total`, `paytrack_http_errors_total`,
`paytrack_http_request_duration_seconds`, and `paytrack_payment_transactions_total`.
Labels use method, known endpoint path, and status code; payment references and IDs
are never labels, preventing high-cardinality metrics.

An example stdout log is:

```json
{"timestamp":"...","level":"INFO","logger":"paytrack","message":"request_completed","method":"POST","path":"/payments","status_code":201,"duration_seconds":0.002}
```

## Run and verify

Use the port-forward in the main README, then open `/docs` for Swagger UI. Confirm
Prometheus targets at `/targets`, Grafana dashboards at port 3000, and container
logs with `kubectl logs -n monitoring-lab deployment/paytrack`.

The readiness failure mode is enabled only with `PAYTRACK_READINESS_FAILURE_MODE=true`
for the controlled failure lab; restore it to `false` after testing.
