.PHONY: environment build format test clean dapp_clean server_storage lorem_example lorem_example_debug dapp_publish_example

VENV_BIN := ./hysail_env/bin

environment:
	. ./scripts/start.sh && ./scripts/build.sh

build:
	./scripts/build.sh

format:
	$(VENV_BIN)/ruff format .
	$(VENV_BIN)/black .

test:
	$(VENV_BIN)/pytest

clean:
	rm -rf output/*
	rm -rf logs/*
	$(MAKE) dapp_clean

dapp_clean:
	rm -rf dapp/contracts/artifacts/*
	rm -rf dapp/contracts/cache/*
	rm -rf dapp/apps/web/src/generated/*
	rm -f dapp/packages/shared/deployments/*.json

server_storage:
	mkdir -p output/server_storage/server_1
	mkdir -p output/server_storage/server_2
	mkdir -p output/server_storage/server_3

lorem_example:
	rm -rf output/*
	rm -rf logs/*
	./scripts/build.sh
	mkdir -p output/server_storage/server_1
	mkdir -p output/server_storage/server_2
	mkdir -p output/server_storage/server_3
	$(VENV_BIN)/hysail encode --server-list examples/server_list_example.json --metadata-output output/ examples/lorem_ipsum.txt
	$(VENV_BIN)/hysail decode --server-file examples/server_list_example.json  output/lorem_ipsum_metadata.pkl --output-file output/

lorem_example_debug:
	rm -rf output/*
	rm -rf logs/*
	./scripts/build.sh
	mkdir -p output/server_storage/server_1
	mkdir -p output/server_storage/server_2
	mkdir -p output/server_storage/server_3
	$(VENV_BIN)/hysail encode --debug --server-list examples/server_list_example.json --metadata-output output/ examples/lorem_ipsum.txt
	$(VENV_BIN)/hysail decode --debug --server-file examples/server_list_example.json  output/lorem_ipsum_metadata.pkl --output-file output/lorem_ipsum_decoded.txt

dapp_publish_example:
	./scripts/build.sh
	mkdir -p output/server_storage/server_1
	mkdir -p output/server_storage/server_2
	mkdir -p output/server_storage/server_3
	$(VENV_BIN)/hysail encode --server-list examples/server_list_example.json --metadata-output output/ examples/hello.txt
	$(VENV_BIN)/hysail publish output/hello_metadata.pkl --deployment-file dapp/packages/shared/deployments/local.json --metadata-uri http://127.0.0.1:8000/manifest --manifest-output output/hello_chain_manifest.json
