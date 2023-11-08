# Provide the path of base OS image here.
FROM ghcr.io/oracle/oraclelinux:8-slim

# Install python and pip.
RUN echo "-internal" > /etc/dnf/vars/ociregion &&\
        microdnf repolist &&\
        microdnf -y update &&\
        microdnf install -y python38 &&\
        microdnf install -y python38-pip &&\
        microdnf clean all

COPY requirements.txt ./

# Rest of this section contains commands to install python dependencies specified in requirement.txt and then setting up python path, docker CMD, Entrypoint etc. These commands should remain same except the pip install which might change depending upon command syntax and the PyPi repository.
RUN	/usr/bin/python3.8 -m pip install --default-timeout=100 --target /python/ --trusted-host=artifactory.oci.oraclecorp.com \
                                          -i https://artifactory.oci.oraclecorp.com/api/pypi/global-release-pypi/simple \
                                          -r requirements.txt

WORKDIR /authorizer
COPY src/authorizer.py /authorizer/
COPY src/utils /authorizer/utils

RUN rm -fr ~/.cache/pip /tmp* .pip_cache /var/cache/ /requirements.txt
RUN mkdir /tmp/

ENV FN_LISTENER=unix:/tmp/lsnr.sock
ENV FN_FORMAT=http-stream
ENV PYTHONPATH=/authorizer:/python:/authorizer/utils
ENV RP_AUTH=true
ENTRYPOINT ["/python/bin/fdk", "/authorizer/authorizer.py", "authorizer"]
