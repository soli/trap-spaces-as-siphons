FROM colomoto/colomoto-docker:next

ADD Benchmark.ipynb /notebook/
ADD trappist /notebook/trappist
ADD models /notebook/models
ADD hard_models /notebook/hard_models
USER root
RUN python3 -m pip install python-sat pyeda
RUN chown -R user:user /notebook/
USER user

MAINTAINER Sylvain Soliman <Sylvain.Soliman@inria.fr>
