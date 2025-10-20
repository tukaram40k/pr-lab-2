import threading
import socket
import time

HOST = '127.0.0.1'
PORT = 8080
REQUESTS = 10

def send_request():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(b'GET /share/index.html HTTP/1.1\r\nHost: localhost\r\n\r\n')
    s.recv(1024)
    s.close()

start = time.time()
threads = [threading.Thread(target=send_request) for _ in range(REQUESTS)]
for t in threads: t.start()
for t in threads: t.join()
elapsed = time.time() - start

print(f"{REQUESTS} requests in {elapsed:.3f}s")