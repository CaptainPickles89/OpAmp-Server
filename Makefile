.PHONY: proto test lint

proto:
	python -m grpc_tools.protoc \
		-I./proto \
		--python_out=. \
		./proto/opamp.proto \
		./proto/anyvalue.proto

test:
	pytest tests/ --cov=opamp_server --cov-report=term-missing

lint:
	ruff check opamp_server/ tests/
	ruff format --check opamp_server/ tests/
