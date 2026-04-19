# HySail

HySail is a Python package and command-line tool for encoding files into packets, distributing those packets across multiple storage servers, and reconstructing the original file from the generated metadata.

It is useful when you want to:

- distribute data across several locations;
- recover the original content from encoded fragments;
- test a simple storage and recovery workflow from the command line.

## Main Commands

After installation, the CLI exposes two core operations:

- **encode**: transforms an input file into packets and distributes them across the configured servers;
- **decode**: reads the metadata and server information to rebuild the original file.

## Requirements

- Python 3.10 or newer
- pip
- a virtual environment is recommended

## Setup by Operating System

### Linux, macOS, or WSL

Create the virtual environment once:

```bash
python3 -m venv .venv
```

Then use the Makefile shortcut:

```bash
make environment
```

This follows the same activation idea used in [scripts/start.sh](scripts/start.sh) and then builds the package.

### Windows PowerShell

Use the manual fallback:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Development Commands

Prefer the Makefile targets whenever `make` is available.

| Task | Preferred command | Notes |
| --- | --- | --- |
| Prepare environment | `make environment` | Activates the project environment and builds the package |
| Build package | `make build` | Uses the repository build flow |
| Format code | `make format` | Keeps Ruff and Black behavior consistent |
| Run tests | `make test` | Runs the pytest suite |
| Clean outputs | `make clean` | Best on Linux, macOS, or WSL |
| Prepare example storage | `make server_storage` | Creates output folders |
| Run example flow | `make lorem_example` | End-to-end encode and decode example |

### Windows note

If `make` is not installed on Windows, use the equivalent fallback commands:

```powershell
pip install -e .
ruff format .
black .
pytest
```

## Docker

A container definition is available in the project root using Ubuntu and Python 3.10.

Build the image:

```bash
docker build -t hysail:local .
```

If your user does not have permission to access Docker, use:

```bash
sudo docker build -t hysail:local .
```

Run the container:

```bash
docker run --rm hysail:local
```

The image installs the package and runs the Makefile test command during the build process. When the container starts, it executes the lorem example flow automatically.

> You need Docker installed on your machine to build and run the image. The Docker CLI is not required inside the Python application itself.

## CLI Usage

Once the environment is activated, the same CLI commands work on Linux, macOS, and Windows.

### Encode a File

```bash
hysail encode --server-list examples/server_list_example.json --metadata-output output/ examples/lorem_ipsum.txt
```

Optional arguments:

- `--block-size`: sets the encoding block size;
- `--server-list`: path to the JSON file that defines the target servers;
- `--metadata-output`: folder where the metadata file will be saved.

### Decode a File

```bash
hysail decode --server-file examples/server_list_example.json output/lorem_ipsum_metadata.pkl --output-file output/
```

Optional arguments:

- `--server-file`: JSON file with the server information required for reconstruction;
- `--output-file`: destination folder for the recovered file.

## Example Workflow

1. Prepare the server list in `examples/server_list_example.json`.
2. Run `hysail encode` on the file you want to distribute.
3. Keep the generated metadata file.
4. Run `hysail decode` later using the metadata and server list.

## Installed Entry Points

The package provides these commands after installation:

- `hysail`: main CLI for encoding and decoding;
- `hysail-test`: runs the project tests through pytest.

