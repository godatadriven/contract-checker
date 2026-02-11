install:
	uv sync --group=dev --group=docs

test:
	$(MAKE) test-unit
	# add any more test groups here to run them all at once using 'make test'

test-unit:
	uv run pytest ./tests/unit

validate-examples:
	uv run contract-checker

validate-custom-examples:
	uv run contract-checker --contract-path tests/fixtures/custom --custom-schema-path tests/fixtures/custom/ecommerce-product-schema.json
