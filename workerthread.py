import struct
from PyQt5.QtCore import pyqtSignal, QThread


class WorkerThread(QThread):
    update_signal = pyqtSignal(int, bytes)

    def __init__(self, client_socket, username):
        super().__init__()
        self.client_socket = client_socket
        self.username = username

    def run(self):
        try:
            while True:
                length = self.client_socket.recv(4)
                mess_len = self.client_socket.recv(4)

                mess_len = int.from_bytes(mess_len, byteorder='big')
                length = int.from_bytes(length, byteorder='big')
                
                received_data = b""
                while len(received_data) < mess_len:
                    tmp = self.client_socket.recv(1024)
                    if not tmp:
                        break
                    received_data += tmp

                print(received_data)
                if not received_data:
                    break
                self.update_signal.emit(length, received_data)
                
        except Exception as e:
            error_message = f"Błąd odbierania danych od serwera: {e}".encode("utf-8")
            print(f"Exception type: {type(e)}")
            print(f"Exception args: {e.args}")
            mess = struct.pack("!5s5s", "TEXT ".encode("utf-8"), self.username.encode("utf-8"))
            self.update_signal.emit(len(mess), mess + error_message)
        finally:
            self.client_socket.close()


    def receive_data_from_server(self):
        data = self.client_socket.recv(1024).decode('utf-8')
        print(data)
        return data
        #
        # try:
        #     while True:
        #         data = client_socket.recv(1024).decode('utf-8')
        #         if not data:
        #             break
        #         self.update_signal.emit(data)
        #
        # except Exception as e:
        #     return (f"Błąd odbierania danych od serwera: {e}")
        # finally:
        #     client_socket.close()