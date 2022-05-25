FROM colomoto/colomoto-docker:2022-05-01

ADD Benchmark.ipynb /notebook/
ADD trappist /notebook/trappist
ADD models /notebook/models
USER root
RUN python3 -m pip install python-sat
RUN chown -R user:user /notebook/
USER user

MAINTAINER Sylvain Soliman <Sylvain.Soliman@inria.fr>
