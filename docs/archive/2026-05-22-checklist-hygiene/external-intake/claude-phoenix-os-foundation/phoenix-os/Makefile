# Phoenix OS — Makefile
# Convenience targets for common development tasks.
# All targets that touch the ISO require root (use `sudo make iso`).

.PHONY: help iso packages clean test dev frontend lint

PHOENIX_VERSION ?= $(shell cat VERSION 2>/dev/null || echo "0.1.0-alpha")

help: ## Show this help
	@echo "Phoenix OS Build Targets"
	@echo "========================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  ISO build requires root: sudo make iso"

iso: ## Build the full live ISO (requires root)
	@echo "Building Phoenix OS ISO v$(PHOENIX_VERSION)..."
	sudo PHOENIX_VERSION=$(PHOENIX_VERSION) ./scripts/build-iso.sh

packages: ## Build all custom .deb packages
	./scripts/package-debs.sh

packages-full: ## Build packages including Tauri apps (slow)
	BUILD_TAURI=1 ./scripts/package-debs.sh

clean: ## Clean build artifacts (keep package cache)
	sudo ./scripts/clean.sh

clean-all: ## Clean everything including package cache and output ISOs
	sudo ./scripts/clean.sh --all --output

verify: ## Verify the build host meets requirements
	./scripts/verify-host.sh

sign: ## Sign the latest built ISO with GPG
	./scripts/sign-iso.sh

test: ## Run all unit tests (no ISO needed)
	@echo "Running unit tests..."
	bash -n scripts/build-iso.sh && echo "  OK: build-iso.sh syntax"
	bash -n scripts/clean.sh && echo "  OK: clean.sh syntax"
	bash -n scripts/verify-host.sh && echo "  OK: verify-host.sh syntax"
	bash -n scripts/package-debs.sh && echo "  OK: package-debs.sh syntax"
	./tests/unit/test-disk-safety.sh
	./tests/unit/test-package-structure.sh

validate: ## Validate the latest built ISO
	./tests/iso-validation/validate-iso.sh output/phoenix-os-*.iso

smoke: ## Run QEMU smoke test on latest built ISO
	./tests/smoke/test-boot.sh output/phoenix-os-*.iso

dev: ## Start phoenix-control-center in Tauri dev mode
	cd apps/phoenix-control-center && cargo tauri dev

frontend: ## Start phoenix-control-center React dev server only
	cd apps/phoenix-control-center && npm run dev

setup: ## Set up developer environment (first-time)
	./scripts/setup-dev.sh

lint: ## Run all linters (cargo fmt, clippy, tsc)
	@echo "Linting Rust (phoenix-control-center)..."
	cd apps/phoenix-control-center && cargo fmt --check && cargo clippy -- -D warnings
	@echo "Linting Rust (phoenix-recovery)..."
	cd apps/phoenix-recovery && cargo fmt --check
	@echo "Type-checking TypeScript (phoenix-control-center)..."
	cd apps/phoenix-control-center && npx tsc --noEmit
	@echo "Checking shell scripts..."
	find . -name "*.sh" | grep -v ".git" | xargs -I{} bash -n {}
	@echo "All lints passed."
