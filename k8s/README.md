# Kubernetes deployment

PayTrack has no Kubernetes API dependency, so its service account deliberately has
no Role or RoleBinding and does not mount a service-account token. This is
least-privilege RBAC: do not grant permissions until the application needs them.

Create the cluster, load the local image, install Metrics Server v0.9.1, then apply:

```powershell
kind create cluster --name observability-lab --config k8s/kind/cluster.yaml
kind load docker-image paytrack:0.1.0 --name observability-lab
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.1/components.yaml
kubectl -n kube-system patch deployment metrics-server --type=json --patch-file k8s/metrics-server-kind-patch.json
kubectl apply -f k8s/base/paytrack.yaml
```

The Secret example is documentation only. Create real local secrets outside Git:

```powershell
kubectl -n monitoring-lab create secret generic paytrack-secrets --from-literal=EXAMPLE_EXTERNAL_API_KEY=local-value
```
