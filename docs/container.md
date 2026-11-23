# Running PayTrack in Docker

## Build

Run the build from the repository root:

```powershell
docker build --tag paytrack:0.1.0 .
```

The image contains only production dependencies. Tests and local virtual-environment
files are excluded by `.dockerignore`.

## Run locally

```powershell
docker run --rm --name paytrack -p 8000:8000 `
  --env PAYTRACK_ENVIRONMENT=local `
  paytrack:0.1.0
```

In another terminal, verify the API and Prometheus endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-WebRequest http://127.0.0.1:8000/metrics
```

Expected health response:

```json
{"status":"healthy"}
```

Stop the foreground container with `Ctrl+C`. When running detached, use
`docker stop paytrack`.

## Validate container health and logs

```powershell
docker inspect --format '{{.State.Health.Status}}' paytrack
docker logs paytrack
```

The health check probes `/health`; it confirms that the application process is
responding. Kubernetes will later use its own liveness and readiness probes,
because readiness has a different traffic-routing purpose.

The application runs as the unprivileged `paytrack` user (UID 10001). Confirm
this with:

```powershell
docker run --rm --entrypoint id paytrack:0.1.0
```
