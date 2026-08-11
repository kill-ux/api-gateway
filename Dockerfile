FROM alpine:3.18

WORKDIR /workspace

RUN apk add --no-cache python3 py3-pip

RUN mkdir -p /workspace/logs

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "server.py"]