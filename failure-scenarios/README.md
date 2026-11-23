# Failure simulation lab

Use only `monitoring-lab`. Watch pods with `kubectl get pods -n monitoring-lab -w`.

## A. CrashLoopBackOff

`kubectl apply -f failure-scenarios/crashloop.yaml`; expect increasing restarts and
`CrashLoopBackOff`. Investigate with `kubectl describe pod -n monitoring-lab -l app=crashloop-demo`
and `kubectl logs -n monitoring-lab -l app=crashloop-demo --previous`. Recover:
`kubectl delete deployment crashloop-demo -n monitoring-lab`.

## B. ImagePullBackOff

`kubectl apply -f failure-scenarios/imagepull.yaml`; expect `ImagePullBackOff`.
Inspect events: `kubectl describe pod -n monitoring-lab -l app=imagepull-demo`.
Recover: `kubectl delete deployment imagepull-demo -n monitoring-lab`.

## C. OOMKilled

`kubectl apply -f failure-scenarios/oomkill.yaml`; expect `OOMKilled` (or failed pod)
because 128Mi allocation exceeds the 64Mi limit. Inspect: `kubectl describe pod oomkill-demo -n monitoring-lab`.
Clean up: `kubectl delete pod oomkill-demo -n monitoring-lab`.

## D. High CPU / HPA

Generate bounded traffic for five minutes:
`kubectl run load --rm -it -n monitoring-lab --image=busybox:1.37.0 -- sh -c 'end=$((SECONDS+300)); while [ $SECONDS -lt $end ]; do wget -q -O- http://paytrack/health >/dev/null; done'`.
Watch `kubectl top pods -n monitoring-lab` and `kubectl get hpa -n monitoring-lab -w`.

## E. Readiness failure

`kubectl -n monitoring-lab patch configmap paytrack-config --type merge -p '{"data":{"PAYTRACK_READINESS_FAILURE_MODE":"true"}}'`; restart with `kubectl rollout restart deployment/paytrack -n monitoring-lab`.
Expect zero ready endpoints. Restore `false`, restart, and run `kubectl get endpointslice -n monitoring-lab -l kubernetes.io/service-name=paytrack`.

## F. Application unavailable

`kubectl scale deployment paytrack -n monitoring-lab --replicas=0`; expect no endpoints and ApplicationDown after its one-minute threshold. Restore: `kubectl scale deployment paytrack -n monitoring-lab --replicas=2`; verify rollout with `kubectl rollout status deployment/paytrack -n monitoring-lab`.
