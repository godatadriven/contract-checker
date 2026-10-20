install:
	uv sync --group=dev --group=docs

test:
	$(MAKE) test-unit
	$(MAKE) test-integration

test-unit:
	uv run pytest ./tests/unit

test-integration:
	uv run pytest ./tests/integration

validate-examples:
	uv run contract-checker --checks-config-path data-contract-checks.example.yml

validate-custom-examples:
	uv run contract-checker --checks-config-path data-contract-checks.example.yml --contract-path tests/fixtures/custom --custom-schema-path tests/fixtures/custom/ecommerce-product-schema.json
