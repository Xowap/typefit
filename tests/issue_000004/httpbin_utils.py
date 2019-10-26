import socket
import time
from multiprocessing import Process
from typing import Text

from httpbin.core import app as httpbin


def wait_for_port(port: int, host: Text = "127.0.0.1", timeout: float = 5.0):
    """
    Wait until a port starts accepting TCP connections.
    """

    start_time = time.perf_counter()

    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def _run(port):
    httpbin.run(host="127.0.0.1", port=port)


class HttpBin:
    def __init__(self, port: int):
        self.port = port
        self.process = None

    def run(self):
        self.process = Process(target=_run, args=(self.port,))
        self.process.start()

    def stop(self):
        if self.process:
            self.process.kill()
            self.process.join()
