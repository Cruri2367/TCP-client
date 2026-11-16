import socket
import struct
import sys

HOST = "127.0.0.1"
PORT = 9000


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            if len(buf) == 0:
                return b""
            raise ConnectionError("Сервер разорвал соединение до конца передачи")
        buf.extend(chunk)
    return bytes(buf)


def send_frame(sock: socket.socket, text: str) -> None:
    data = text.encode("utf-8")
    header = struct.pack("!I", len(data))
    sock.sendall(header + data)


def recv_frame(sock: socket.socket) -> str:
    header = recv_exact(sock, 4)
    if not header:
        raise ConnectionError("Пустой ответ: сервер закрыл соединение")
    (msg_len,) = struct.unpack("!I", header)
    body = recv_exact(sock, msg_len)
    if len(body) < msg_len:
        raise ConnectionError("Неполный ответ от сервера")
    return body.decode("utf-8")


def main():
    expressions = [
        "12+30*2",
        "100/4",
        "(" + " + ".join(["1"] * 200) + ") * 5",
        "10 / 0",
    ]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print(f"Подключено к {HOST}:{PORT}\n")

            for expr in expressions:
                send_frame(s, expr)
                reply = recv_frame(s)
                display_expr = expr if len(expr) < 30 else expr[:27] + "..."
                print(f"Запрос: {display_expr:<30} -> Ответ: {reply}")

    except ConnectionRefusedError:
        print("Ошибка (ECONNREFUSED): сервер недоступен или не запущен на порту 9000.")
        sys.exit(1)
    except TimeoutError:
        print("Ошибка (ETIMEDOUT): превышено время ожидания ответа от сервера.")
        sys.exit(1)
    except ConnectionError as e:
        print(f"Ошибка соединения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()