#!/usr/bin/env sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
THESIS_DIR="$REPO_ROOT/private/thesis"

cd "$THESIS_DIR"

pdflatex monografia.tex
bibtex monografia
makeglossaries monografia
pdflatex monografia.tex
pdflatex monografia.tex
