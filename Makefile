.PHONY: cluster monitoring app load analyze grafana prometheus policies clean

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

grafana:
	kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80

prometheus:
	kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090

policies:
	kubectl apply -f policies/

clean:
	kind delete cluster --name costpilot
