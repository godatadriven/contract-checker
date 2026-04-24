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
	uv run contract-checker

validate-custom-examples:
	uv run contract-checker --contract-path tests/fixtures/custom --custom-schema-path tests/fixtures/custom/ecommerce-product-schema.json
