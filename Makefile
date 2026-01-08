.PHONY: run-engine run-dashboard proof

run-engine:
	./scripts/run_engine.sh

run-dashboard:
	./scripts/run_dashboard.sh

proof:
	./scripts/proof_check.sh
