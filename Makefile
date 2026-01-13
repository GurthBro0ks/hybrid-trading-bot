.PHONY: run-engine run-dashboard proof test-venuebook

run-engine:
	./scripts/run_engine.sh

run-dashboard:
	./scripts/run_dashboard.sh

proof:
	./scripts/proof_check.sh

test-venuebook:
	cd engine-rust && cargo test --test test_venuebook_normalization
