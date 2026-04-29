.PHONY: environment build format test clean server_storage lorem_example dapp_publish_example

environment:
	. ./scripts/start.sh && ./scripts/build.sh

build:
	./scripts/build.sh

format:
	ruff format .
	black .

test:
	pytest

clean:
	rm -rf output/*
	rm -rf logs/*

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
	hysail encode --server-list examples/server_list_example.json --metadata-output output/ examples/lorem_ipsum.txt
	hysail decode --server-file examples/server_list_example.json  output/lorem_ipsum_metadata.pkl --output-file output/

lorem_example_debug_time:
	rm -rf output/*
	rm -rf logs/*
	./scripts/build.sh
	mkdir -p output/server_storage/server_1
	mkdir -p output/server_storage/server_2
	mkdir -p output/server_storage/server_3
	hysail encode --debug-time --server-list examples/server_list_example.json --metadata-output output/ examples/lorem_ipsum.txt
	hysail decode --debug-time --server-file examples/server_list_example.json  output/lorem_ipsum_metadata.pkl --output-file output/lorem_ipsum_decoded.txt

dapp_publish_example:
	./scripts/build.sh
	mkdir -p output/server_storage/server_1
	mkdir -p output/server_storage/server_2
	mkdir -p output/server_storage/server_3
	hysail encode --server-list examples/server_list_example.json --metadata-output output/ examples/hello.txt
	hysail publish output/hello_metadata.pkl --deployment-file dapp/packages/shared/deployments/local.json --metadata-uri http://127.0.0.1:8000/manifest --manifest-output output/hello_chain_manifest.json
