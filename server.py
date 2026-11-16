import ast
import operator
import socket
import struct

HOST = "127.0.0.1"
PORT = 9000

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(expr: str) -> str:
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Неподдерживаемая операция")

    try:
        tree = ast.parse(expr.strip(), mode="eval")
        res = _eval(tree.body)
        return str(int(res) if isinstance(res, float) and res.is_integer() else res)
    except ZeroDivisionError:
        return "ERR: деление на ноль"
    except Exception as e:
        return f"ERR: ошибка синтаксиса ({e})"


def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Читает ровно n байт из потока или возвращает пустую строку при EOF."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            if len(buf) == 0:
                return b""
            raise ConnectionError("Обрыв соединения посреди сообщения")
        buf.extend(chunk)
    return bytes(buf)


def send_frame(sock: socket.socket, text: str) -> None:
    data = text.encode("utf-8")
    header = struct.pack("!I", len(data))
    sock.sendall(header + data)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        print(f"Сервер запущен на {HOST}:{PORT}...")

        while True:
            conn, addr = srv.accept()
            print(f"Подключился клиент: {addr}")
            with conn:
                while True:
                    try:
                        header = recv_exact(conn, 4)
                        if not header:
                            print(f"Клиент {addr} закрыл соединение.")
                            break
                        (msg_len,) = struct.unpack("!I", header)
                        body = recv_exact(conn, msg_len)
                        if not body:
                            break
                        expr = body.decode("utf-8")
                        print(f"[{addr}] Запрос: {expr!r}")

                        answer = safe_eval(expr)
                        send_frame(conn, answer)
                    except (ConnectionError, OSError) as e:
                        print(f"Ошибка связи с {addr}: {e}")
                        break


if __name__ == "__main__":
    main()