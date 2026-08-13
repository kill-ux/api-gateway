FROM spectolabs/hoverfly:v1.12.11
ARG MOCK_FILE

RUN adduser -D appuser
USER appuser

COPY mocks/${MOCK_FILE}.json /hoverfly/${MOCK_FILE}.json

HEALTHCHECK --interval=5s --timeout=3s --start-interval=1s --retries=5 \
    CMD wget -q -O- http://127.0.0.1:3000/health