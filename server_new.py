import os
import sys
import socket
import mimetypes
import threading
import time

HOST = '0.0.0.0'
PORT = 8080
BUFFER_SIZE = 1024

# hit counter dict
file_access_counts = {}
# lock for syncing
file_counter_lock = threading.Lock()

def build_http_response(status_code, content_type=None, content=None):
    status_messages = {
        200: "OK",
        404: "Not Found"
    }
    status_line = f"HTTP/1.1 {status_code} {status_messages[status_code]}\r\n"

    headers = ""
    if content_type:
        headers += f"Content-Type: {content_type}\r\n"
    if content:
        headers += f"Content-Length: {len(content)}\r\n"
    headers += "Connection: close\r\n\r\n"

    if content:
        return status_line.encode() + headers.encode() + content
    else:
        return status_line.encode() + headers.encode()

def increment_file_counter(file_path):
    # use lock
    with file_counter_lock:
        if file_path in file_access_counts:
            current_count = file_access_counts[file_path]
            time.sleep(0.001)
            file_access_counts[file_path] = current_count + 1
        else:
            file_access_counts[file_path] = 1

def generate_directory_listing(dir_path, base_dir, request_path):
    """Generate an HTML page listing directory contents recursively with access counts."""
    entries = os.listdir(dir_path)
    entries.sort()

    html = ["<html><body>"]
    html.append(f"<h2>Directory listing for {request_path}</h2>")
    html.append("<table border='1' style='border-collapse: collapse;'>")
    html.append("<tr><th>Name</th><th>Type</th><th>Times Served</th></tr>")

    parent_path = os.path.dirname(request_path.rstrip('/'))
    if not parent_path:
        parent_path = '/'
    if not parent_path.endswith('/'):
        parent_path += '/'
    html.append(f'<tr><td><a href="{parent_path}">../</a></td><td>Directory</td><td>-</td></tr>')

    for name in entries:
        full_path = os.path.join(dir_path, name)
        display_name = name + '/' if os.path.isdir(full_path) else name
        file_type = "Directory" if os.path.isdir(full_path) else "File"

        href = (request_path.rstrip('/') + '/' + name).replace('\\', '/')
        if os.path.isdir(full_path):
            href += '/'

        # use lock
        with file_counter_lock:
            access_count = file_access_counts.get(full_path, 0)
        
        html.append(f'<tr><td><a href="{href}">{display_name}</a></td><td>{file_type}</td><td>{access_count}</td></tr>')

    html.append("</table></body></html>")
    return "\n".join(html).encode("utf-8")

def handle_request(conn, base_dir):
    time.sleep(1)

    try:
        request = conn.recv(BUFFER_SIZE).decode()
        if not request:
            return

        request_line = request.split('\n')[0]
        parts = request_line.split()
        if len(parts) < 2:
            return

        method, path = parts[0], parts[1]
        if method != "GET":
            return

        requested_path = path.lstrip('/')
        safe_path = os.path.normpath(os.path.join(base_dir, requested_path))

        if not safe_path.startswith(os.path.abspath(base_dir)):
            response = build_http_response(404)
            conn.sendall(response)
            return

        if path == '/' and os.path.isdir(base_dir):
            content = generate_directory_listing(base_dir, base_dir, path)
            response = build_http_response(200, "text/html", content)
            conn.sendall(response)
            return

        if os.path.isdir(safe_path):
            content = generate_directory_listing(safe_path, base_dir, path)
            response = build_http_response(200, "text/html", content)
            conn.sendall(response)
            return

        if not os.path.isfile(safe_path):
            response = build_http_response(404)
            conn.sendall(response)
            return

        content_type, _ = mimetypes.guess_type(safe_path)
        if content_type not in ["text/html", "image/png", "application/pdf"]:
            increment_file_counter(safe_path)

            with open(safe_path, 'rb') as f:
                content = f.read()

            response = build_http_response(200, "text/html", content)
            conn.sendall(response)
            return

        increment_file_counter(safe_path)

        with open(safe_path, 'rb') as f:
            content = f.read()

        response = build_http_response(200, content_type, content)
        conn.sendall(response)
    finally:
        conn.close()

def server_start(base_dir):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"serving '{base_dir}' at http://{HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            print(f"new socket {addr}")
            thread = threading.Thread(target=handle_request, args=(conn, base_dir))
            thread.start()
            print(f"thread started for {addr}")

if len(sys.argv) != 2:
    print("python server.py <dir_to_serve>")
    sys.exit(1)

directory = sys.argv[1]
if directory == '/':
    directory = os.getcwd()
if not os.path.isdir(directory):
    print("bad dir")
    sys.exit(1)

server_start(os.path.abspath(directory))