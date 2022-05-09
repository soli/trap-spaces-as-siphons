FROM colomoto/colomoto-docker:2022-05-01

ADD trappist.py Benchmark.ipynb /notebook/
ADD models /notebook/models
USER root
RUN chown -R user:user /notebook/
USER user

MAINTAINER Sylvain Soliman <Sylvain.Soliman@inria.fr>
