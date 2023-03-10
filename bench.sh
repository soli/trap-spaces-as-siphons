#!/usr/bin/env bash

docker build -t trappist $(dirname -- ${BASH_SOURCE[0]})
docker run -v $(pwd):/notebook/work trappist jupyter nbconvert --to notebook --output work/Benchmark-TCS-Random.ipynb --execute --allow-errors Benchmark-TCS-Random.ipynb
