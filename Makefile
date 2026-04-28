.DEFAULT_GOAL := help
.PHONY: help clean publish publish-test

# Colours
BOLD  := \033[1m
RESET := \033[0m
CYAN  := \033[36m

# Maintainers need `pip install build twine` to run the publish targets.

help:  ## Show this help message
	@printf "$(BOLD)MaldiSuite - available targets$(RESET)\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'

# Housekeeping

clean:  ## Remove build artefacts and caches
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info"   -exec rm -rf {} + 2>/dev/null || true
	@rm -rf dist/ build/ .ruff_cache/

# Release

publish: clean  ## Build and publish package to PyPI
	@read -p "Publish to PyPI? [y/N] " ans && [ "$$ans" = "y" ]
	@python -m build
	@twine upload dist/*

publish-test: clean  ## Build and publish package to TestPyPI
	@python -m build
	@twine upload --repository testpypi dist/*
