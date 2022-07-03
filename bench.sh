#!/usr/bin/env bash

docker build -t trappist $(dirname -- ${BASH_SOURCE[0]})
docker run -it trappist jupyter nbconvert --to asciidoc --stdout --execute Benchmark.ipynb
