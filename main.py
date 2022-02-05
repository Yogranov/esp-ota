import socket
from time import sleep
import os
import json
import re 
import pathlib

# Print and exit, holds the window open
def dd(misc):
    print(misc)
    input("\nPress ENTER key to exit...")
    exit()

# Load configs from json file
project_dir = str(pathlib.Path(__file__).parent.resolve())
f = open(project_dir + '/config.json')
if not f:
    dd("Config file not found")

json_config = json.load(f)

# Configs
ESP_IP         = json_config["esp_ip"]
PORT           = json_config["port"]
FILE           = json_config["bin_path"]

try:
    DISABLE_SCRIPT = json_config["disable_script"]
except KeyError:
    DISABLE_SCRIPT = False

# Constans
DOWNLOAD_BATCH         = 1024
FILE_MIN_SIZE          = 100     * 1000    # 100kb
FILE_MAX_SIZE          = 3       * 1000000 # 3MB
FILE_ALLOWED_EXTENSION = ".bin"

try:
    file_size = os.path.getsize(FILE)
except:
    dd("Bin file error, please check file path")

PREPERE_MESSAGE = f'0 {PORT} {str(file_size)} 0' + 'a' * 40 # identity message, must be at least 44 charechters


# Send UDP packet to ESP make it start request data from the tcp server
def identity_phase():
    SOCKET_TIMEOUT_DURATION = 3 #seconds

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(SOCKET_TIMEOUT_DURATION)

    try:
        udp_socket.sendto(PREPERE_MESSAGE.encode(), (ESP_IP, PORT))
        data, address = udp_socket.recvfrom(DOWNLOAD_BATCH)

    except socket.timeout:
        print("Socket timeout, check ESP ip and port")
        return False

    udp_socket.close()

    if data:
        print(f"ESP with ip {address} got the request and ready to OTA")
    else:
        print("ESP not found, aborting...")
        return False

    return True


# Open tcp server and response to ESP with new bin file
def transfer_data():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("", PORT))

    tcp_socket.listen(1)
    conn, addr = tcp_socket.accept()
    file = open(FILE, "rb")
    file_part = file.read(DOWNLOAD_BATCH)

    print('Connected by', addr)
    while True:
        try:
            conn.send(file_part)
            file_part = file.read(DOWNLOAD_BATCH)

            data = conn.recv(DOWNLOAD_BATCH)
            if not data:
                print("OTA done")
                break

        except socket.error:
            print ("Error Occurred")
            break

    conn.close()


def config_validate():
    IP_REGEX = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    VALID_PORTS = [3232, 8266]

    if file_size < FILE_MIN_SIZE or file_size > FILE_MAX_SIZE:
        print("Wrong file size")
        return False

    if not FILE[-4:] == (FILE_ALLOWED_EXTENSION):
        print("Wrong file extention")
        return False

    if not re.match(IP_REGEX, ESP_IP):
        print("Wrong IP format")
        return False

    if PORT not in VALID_PORTS:
        print("Port not valid")
        return False

    return True


# Program starts here
if __name__ == "__main__":
    if DISABLE_SCRIPT:
        exit()

    if not config_validate():
        dd("Config validate failed, aborting...")

    if identity_phase():
        sleep(1)
        transfer_data()

    else:
        dd("Identity phase error, aborting...")

    dd("All done :)")