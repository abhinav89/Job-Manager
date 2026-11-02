FROM python:3.12-slim-bookworm AS base

FROM base AS python
COPY cv_tailor/sandbox/worker.py /opt/worker.py
ENTRYPOINT ["python", "-I", "/opt/worker.py"]

FROM base AS pdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fontconfig libfontconfig1 fonts-lmodern \
    texlive-xetex texlive-latex-extra texlive-fonts-extra texlive-fonts-recommended lmodern fonts-font-awesome \
    && rm -rf /var/lib/apt/lists/*
RUN python -c "import urllib.request,tarfile,io; data=urllib.request.urlopen('https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz',timeout=60).read(); t=tarfile.open(fileobj=io.BytesIO(data)); open('/usr/local/bin/tectonic','wb').write(t.extractfile('tectonic').read())" \
    && chmod 755 /usr/local/bin/tectonic
ENV TECTONIC_CACHE_DIR=/opt/tectonic-cache XDG_CACHE_HOME=/opt/tex-cache
COPY services/templates /opt/templates
COPY cv_tailor/sandbox/prewarm.py /opt/prewarm.py
RUN python /opt/prewarm.py && chmod -R a+rX /opt/tectonic-cache /opt/tex-cache && rm -rf /tmp/*

COPY cv_tailor/sandbox/worker.py /opt/worker.py
ENTRYPOINT ["python", "-I", "/opt/worker.py"]
