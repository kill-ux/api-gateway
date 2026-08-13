FROM spectolabs/hoverfly:v1.12.11
ARG MOCK_FILE

RUN adduser -D appuser
USER appuser

COPY mocks/${MOCK_FILE}.json /hoverfly/${MOCK_FILE}.json