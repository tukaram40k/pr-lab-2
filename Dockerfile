FROM python:3.11-slim

WORKDIR /app

COPY server.py .
COPY client.py .
COPY share ./share

EXPOSE 8080

CMD ["python", "-u", "server.py", "share"]
