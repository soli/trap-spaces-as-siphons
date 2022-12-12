FROM colomoto/colomoto-docker:2022-12-01
LABEL maintainer="Sylvain Soliman <Sylvain.Soliman@inria.fr>"

HEALTHCHECK --interval=1m CMD curl -f http://localhost:8888 || exit 1

RUN mkdir /tmp/trappist
COPY setup.cfg setup.py pyproject.toml /tmp/trappist
COPY --chown=user:user models /notebook/models
COPY --chown=user:user hard_models /notebook/hard_models
COPY --chown=user:user Benchmark.ipynb /notebook/
COPY trappist /tmp/trappist/trappist
USER root
RUN python3 -m pip install -e /tmp/trappist
USER user
