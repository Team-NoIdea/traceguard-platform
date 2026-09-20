FROM ubuntu:24.04
ARG CODEQL_VERSION=2.27.0
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl unzip python3 git && rm -rf /var/lib/apt/lists/*
RUN curl -fL --retry 3 https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.zip -o /tmp/codeql.zip && unzip -q /tmp/codeql.zip -d /opt && rm /tmp/codeql.zip
ENV PATH=/opt/codeql:$PATH
ENV CODEQL_PACK_DOWNLOAD_LOCATION=/opt/codeql-packs
RUN codeql pack download --dir=/opt/codeql-packs codeql/python-queries@1.8.10
RUN codeql pack download --dir=/opt/codeql-packs codeql/javascript-queries@2.4.5
COPY scan.py /opt/traceguard/scan.py
COPY scan.sh /opt/traceguard/scan.sh
RUN chmod 755 /opt/traceguard/scan.sh
USER 1000:1000
ENTRYPOINT ["/bin/sh", "/opt/traceguard/scan.sh"]
