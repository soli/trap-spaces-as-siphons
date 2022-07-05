#!/usr/bin/env bash

docker build -t trappist $(dirname -- ${BASH_SOURCE[0]})
docker run -v $(pwd):/notebook/work trappist jupyter nbconvert --to notebook --output work/Benchmark.ipynb --execute Benchmark.ipynb
