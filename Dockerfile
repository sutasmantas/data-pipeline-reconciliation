FROM python@sha256:8edbf9e42c7fb168b9c523718ed907117e6d2e60f5889c0c499bbda3a787da53

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY vendor/ ./vendor/
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY sql_database/ ./sql_database/
COPY contracts/ ./contracts/
COPY fixtures/ ./fixtures/

RUN python -m pip install --no-cache-dir \
      vendor/adapterproof-0.2.0-py3-none-any.whl \
      vendor/deliveryguard-0.2.0-py3-none-any.whl \
    && python -m pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 pipelineforge \
    && mkdir /data \
    && chown -R pipelineforge:pipelineforge /app /data

USER pipelineforge
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"

ENTRYPOINT ["pipelineforge"]
CMD ["serve", "--evidence-dir", "/data/evidence", "--host", "0.0.0.0", "--port", "8080"]
