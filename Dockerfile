FROM python:3.12-slim

LABEL org.opencontainers.image.title="helmi-devsecops-scanner" \
      org.opencontainers.image.description="Local DevSecOps scanner: Checkov + Tfsec + Gitleaks + Ansible-Lint" \
      org.opencontainers.image.source="https://github.com/F0CUSMSK/devsecops-pipeline"

# git is required for Gitleaks full-history scanning
RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Python-based scanners (same install path as the CI pipeline)
RUN pip install --no-cache-dir checkov ansible-lint ansible

# Go binaries pinned to the exact versions used in the CI pipeline
ARG TFSEC_VERSION=1.28.14
ARG GITLEAKS_VERSION=8.24.3
RUN curl -fsSLo tfsec "https://github.com/aquasecurity/tfsec/releases/download/v${TFSEC_VERSION}/tfsec-linux-amd64" \
 && install -m 0755 tfsec /usr/local/bin/tfsec \
 && curl -fsSLo gitleaks.tar.gz "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
 && tar -xzf gitleaks.tar.gz gitleaks \
 && install -m 0755 gitleaks /usr/local/bin/gitleaks \
 && rm -f tfsec gitleaks.tar.gz

# mounted host repos are owned by another uid - allow git to read them
RUN git config --global --add safe.directory '*'

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /code
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
