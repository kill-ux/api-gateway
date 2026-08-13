FROM alpine:3.18

WORKDIR /workspace

RUN apk add --no-cache python3 py3-pip && \
    mkdir -p /workspace/logs && \
    adduser -D appuser

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./server.py ./server.py

RUN chown -R appuser:appuser /workspace
USER appuser

ENTRYPOINT ["python3", "server.py"]

HEALTHCHECK --interval=5s --timeout=3s --start-interval=1s --retries=5 \
    CMD wget -q -O- http://127.0.0.1:3000/health