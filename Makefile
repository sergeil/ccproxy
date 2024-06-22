setup-dev:
	pipenv sync --dev

setup:
	deployment/bin/setup.sh

shell:
	pipenv shell

mypy:
	mypy ccproxy tests --strict

lint:
	ruff check .

test:
	AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=local python -m pytest --capture=tee-sys -m "not real_cc_server" --verbose

test-cc-server:
	AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=local python -m pytest --capture=tee-sys -m real_cc_server

local-db:
	./docker/start-dynamodb.sh

build-package:
	./deployment/bin/build-package.sh

build-layer:
	./deployment/bin/build-layer.sh

infra:
	cd deployment && terraform apply $(OPTS)

destroy-infra:
	./deployment/bin/destroy-infra.sh

generate-db-key:
	@python ccproxy/cli.py generate-db-key