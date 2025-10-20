FROM python:3.11-slim

WORKDIR /app

COPY server_new.py .
COPY client_new.py .
COPY share ./share

EXPOSE 8080

CMD ["python", "-u", "server_new.py", "/"]
