from time import sleep
import os
import pathlib
import re
import socket


class Dota:
    DOWNLOAD_BATCH = 1024
    FILE_MIN_SIZE = 100 * 1000  # 100kb
    FILE_MAX_SIZE = 3 * 1000000  # 3MB
    FILE_ALLOWED_EXTENSION = ".bin"
    VALID_PORTS = [3232, 8266]
    IP_PATTERN = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    SOCKET_TIMEOUT_SECS = 3  # seconds

    def __init__(self, ip, filename, port=3232):
        self._ip = ip
        self._port = port
        self._fw_size = 0
        self._filename = filename
        self._validate()
        self._tcp_socket = self.tcp_socket()

    def _validate(self):
        self._file_size = os.path.getsize(self._filename)
        if self._file_size < Dota.FILE_MIN_SIZE or self._file_size > Dota.FILE_MAX_SIZE:
            return False

        if not pathlib.Path(self._filename).suffix == Dota.FILE_ALLOWED_EXTENSION:
            raise ValueError(
                f"FW file must be a {Dota.FILE_ALLOWED_EXTENSION} file")

        if not re.match(Dota.IP_PATTERN, self._ip):
            raise ValueError(f"Wrong IP format")

        if self._port not in Dota.VALID_PORTS:
            raise ValueError(
                f"Invalid port, received: {self._port}, valid values: {Dota.VALID_PORTS}")

    def start_dota(self):
        try:
            res = self._identify()
            if not res:
                return res
            sleep(1)
            res = self._transfer_data()
        except Exception as e:
            print(e)
            res = False
        return res

    def _identify(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(Dota.SOCKET_TIMEOUT_SECS)
        # identity message, must be at least 44 charechters
        message = (f"0 {self._port} {str(self._file_size)} 0" + "a" * 40)

        try:
            udp_socket.sendto(message.encode(), (self._ip, self._port))
            data, address = udp_socket.recvfrom(Dota.DOWNLOAD_BATCH)
        except socket.timeout:
            udp_socket.close()
            print("Socket timeout, check ESP ip and port")
            return False

        if not data:
            print("ESP not found, aborting...")
            return False

        print(f"ESP with ip {address} got the request and ready to OTA")
        return True

    def tcp_socket(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(("", self._port))
        tcp_socket.listen(1)
        return tcp_socket

    def _transfer_data(self):
        conn, addr = self._tcp_socket.accept()
        f = open(self._filename, "rb")
        file_part = f.read(Dota.DOWNLOAD_BATCH)

        print("Connected by", addr)
        print(f"[DirectOta] starting OTA")
        res = True
        while True:
            try:
                conn.send(file_part)
                file_part = f.read(Dota.DOWNLOAD_BATCH)
                data = conn.recv(Dota.DOWNLOAD_BATCH)
                if not data:
                    print("[DirectOta] OTA done")
                    break
            except socket.error:
                print("Error Occurred")
                res = False
                break
        conn.close()
        return res


if __name__ == "__main__":
    # dota = Dota("192.168.41.16",".pio/build/staging/firmware2.bin")
    # dota.start_dota()
    pass
