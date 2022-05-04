FROM colomoto/colomoto-docker:2022-05-01

ADD trappist.py models.tgz Benchmark.ipynb /notebook/
USER root
RUN chown -R user:user /notebook/
USER user

MAINTAINER Sylvain Soliman <Sylvain.Soliman@inria.fr>
