FROM alpine:3.18

WORKDIR /app

RUN apk add --no-cache python3 py3-pip

RUN mkdir -p /app/logs

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "server.py"]