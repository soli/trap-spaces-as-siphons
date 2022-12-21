FROM colomoto/colomoto-docker:2022-12-01
LABEL maintainer="Sylvain Soliman <Sylvain.Soliman@inria.fr>"

HEALTHCHECK --interval=1m CMD curl -f http://localhost:8888 || exit 1

RUN mkdir /tmp/trappist
COPY pyproject.toml LICENSE README.md /tmp/trappist/
COPY --chown=user:user models /notebook/models
COPY --chown=user:user hard_models /notebook/hard_models
COPY --chown=user:user Benchmark.ipynb /notebook/
COPY trappist /tmp/trappist/trappist

# install minizinc
ENV MINIZINC_VERSION=2.6.4
RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/${MINIZINC_VERSION}/MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64.tgz \
       && tar xzf MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64.tgz \
       && rm -Rf MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64.tgz \
       && mv MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64 Minizinc
ENV PATH=$PATH:/notebook/Minizinc/bin

USER root

RUN python3 -m pip install -U pip
RUN python3 -m pip install -e /tmp/trappist

USER user
