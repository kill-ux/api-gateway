FROM spectolabs/hoverfly:latest
ARG MOCK_FILE

RUN adduser -D appuser
USER appuser

COPY mocks/${MOCK_FILE}.json /hoverfly/${MOCK_FILE}.json