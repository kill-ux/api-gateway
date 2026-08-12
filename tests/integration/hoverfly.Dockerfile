FROM spectolabs/hoverfly:latest
ARG MOCK_FILE
COPY mocks/${MOCK_FILE}.json /hoverfly/${MOCK_FILE}.json