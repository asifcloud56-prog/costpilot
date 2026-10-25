.PHONY: cluster monitoring app load load-before apply load-after compare reset-app analyze grafana prometheus policies clean

cluster:
	bash cluster/setup.sh

monitoring:
	bash monitoring/install.sh

app:
	docker build -t costpilot-demo:0.1 apps/demo-app
	kind load docker-image costpilot-demo:0.1 --name costpilot
	kubectl apply -f apps/demo-app/k8s/

load:
	k6 run loadtest/k6-script.js

analyze:
	pip install -q -r analysis/requirements.txt
	python3 analysis/rightsize.py --namespace demo

# ---- Before/after validation workflow --------------------------------------
# 1. make reset-app     deploy the original (oversized) requests
# 2. make load-before   load test + snapshot of requests  -> results/before_*.json
# 3. make analyze       build analysis/report.csv         (needs `make prometheus`)
# 4. make apply         apply recommended requests, wait for rollout
# 5. make load-after    load test + snapshot of requests  -> results/after_*.json
# 6. make compare       before/after table                -> results/comparison.md

reset-app:
	kubectl apply -f apps/demo-app/k8s/
	kubectl -n demo rollout status deployment/demo-app --timeout=180s

load-before:
	mkdir -p results
	kubectl -n demo get deployment demo-app -o json > results/before_deploy.json
	k6 run --summary-export=results/before_k6.json loadtest/k6-script.js

apply:
	python3 analysis/apply.py --namespace demo --deployment demo-app --container app

load-after:
	mkdir -p results
	kubectl -n demo get deployment demo-app -o json > results/after_deploy.json
	k6 run --summary-export=results/after_k6.json loadtest/k6-script.js

compare:
	python3 analysis/compare.py

# ---- Port-forwards and misc ------------------------------------------------

grafana:
	kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80

prometheus:
	kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090

policies:
	kubectl apply -f policies/

clean:
	kind delete cluster --name costpilot
