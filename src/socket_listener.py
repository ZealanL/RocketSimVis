import socket

import state_manager
import json

import time

class SocketListener:
    has_received: bool = False
    buffer_size: int = 1024 * 1024

    def run(self, port_num: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', port_num))
        print("Created socket on port {}, listening...".format(port_num))
        prev_recv_time = time.time()
        while True:
            has_received: True

            data, addr = sock.recvfrom(self.buffer_size)
            j = json.loads(data.decode("utf-8"))

            recv_time = time.time()

            with state_manager.global_state_mutex:
                state_manager.global_state_manager.state.read_from_json(j)
                state_manager.global_state_manager.state.recv_time = recv_time
                state_manager.global_state_manager.state.recv_interval = recv_time - prev_recv_time

            prev_recv_time = time.time()