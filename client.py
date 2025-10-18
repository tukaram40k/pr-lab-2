import sys
import socket
import os

BUFFER_SIZE = 4096

def client_request(host, port, url_path, save_dir):
    # Make sure save directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, int(port)))

        # Send HTTP GET request
        request = f"GET {url_path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode())

        # Receive response
        response = b""
        while True:
            data = s.recv(BUFFER_SIZE)
            if not data:
                break
            response += data

    # Split headers and body
    header_data, _, body = response.partition(b"\r\n\r\n")
    headers = header_data.decode(errors="ignore").split("\r\n")

    # Get content type
    content_type = None
    for h in headers:
        if h.lower().startswith("content-type"):
            content_type = h.split(":", 1)[1].strip()
            break

    # Handle based on content type
    if content_type is None:
        print("no content-type found")
        print(response.decode(errors="ignore"))
        return

    if content_type.startswith("text/html"):
        print(body.decode(errors="ignore"))

    elif content_type in ["application/pdf", "image/png"]:
        # Derive filename from URL path
        filename = os.path.basename(url_path)
        if not filename:
            filename = "downloaded_file"

        file_path = os.path.join(save_dir, filename)
        with open(file_path, "wb") as f:
            f.write(body)
        print(f"saved {filename} in {save_dir}")

    else:
        print(f"bad content type: {content_type}")

if len(sys.argv) != 5:
    print("python client.py <server_host> <server_port> <url_path> <save_dir>")
    sys.exit(1)

host, port, url_path, save_dir = sys.argv[1:]
client_request(host, port, url_path, save_dir)
