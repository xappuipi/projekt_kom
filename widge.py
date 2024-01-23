import struct
import sys
import threading
import socket
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPlainTextEdit, QScrollArea, QPushButton, \
    QHBoxLayout, QFileDialog
from PyQt5 import QtGui

from workerthread import WorkerThread
import keyboard

class ScrollLabel(QScrollArea):

    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        self.setWidgetResizable(True)

        self.cont = QWidget(self)
        self.setWidget(self.cont)

        self.layout = QVBoxLayout(self.cont)
        self.layout_wiad = QVBoxLayout(self.cont)
        self.label = QLabel(self.cont)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label.setWordWrap(True)
        self.layout_wiad.addWidget(self.label)
        self.layout_wiad.setAlignment(Qt.AlignTop)
        self.layout.addLayout(self.layout_wiad, 1)
        
    
    def check_type(self, length, data):
        header = data[:length]
        data = data[length:]
        n = len(header) - 5

        data_type, username = struct.unpack(f'!5s{n}s', header)
        data_type = data_type.decode('utf-8').strip()

        if data_type.strip() == "TEXT":
            self.setText(username.decode("utf-8") + ": " + data.decode('utf-8'))
        elif data_type == "IMAGE":
            self.show_image(data)
        else:
            print(f"Unknown message type: {header}")

    def setText(self, text, reversed=False):
        self.label = QLabel(text)

        if reversed: self.label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        else: self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.layout_wiad.addWidget(self.label)

        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


    def show_image(self, image, reversed=False):
        self.label = QLabel()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image)
        self.label.setPixmap(pixmap)

        if reversed: self.label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        else: self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.layout_wiad.addWidget(self.label)

        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


    def get_text(self):
        te = self.label.text()
        return te



class MojWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def __del__(self):
        self.client_socket.close()

    zapytania = ["Podaj adres IP: ", "Podaj port: ", "Podaj nazwe użytkownika: "]
    i = 1
    odpowiedzi = []

    def initUI(self):
        layout = QVBoxLayout()

        label = QLabel('Dzień dobry!', self)


        self.text_input = QPlainTextEdit(self)
        self.text_input.textChanged.connect(self.onTextChanged)
        self.text_input.keyPressEvent = self.on_key_pressed

        self.wiadomosci = ScrollLabel(self)


        self.przycisk_dodaj = QPushButton("Dodaj zdjęcie", self)
        self.przycisk_dodaj.clicked.connect(self.wyslij_zdj)

        layout.addWidget(label)
        layout.addWidget(self.wiadomosci, 50)

        self.wiadomosci.setText(self.zapytania[0])

        layout_text = QHBoxLayout()
        layout_text.addWidget(self.text_input, 100)
        layout_text.addWidget(self.przycisk_dodaj, 1)
        layout_text.addStretch(1)

        layout.addLayout(layout_text)

        self.setLayout(layout)

        # Ustawianie układu dla widgetu głównego
        self.setLayout(layout)

        self.setWindowTitle('Kominikator (by T.Mickiewicz)')
        self.setGeometry(100, 100, 600, 700)

        self.pending = None

    def onTextChanged(self):
        self.pending = self.text_input.toPlainText()

    def on_key_pressed(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            cursor = self.text_input.textCursor()
            cursor.insertText('\n')
        elif event.key() == Qt.Key_Return:
            self.wyslij()
        else:
            QPlainTextEdit.keyPressEvent(self.text_input, event)

    def wyslij(self):
        self.wiadomosci.setText(self.pending, reversed=True)
        if self.i <= 3:
            self.odpowiedzi.append(self.pending.strip())
            if self.i < 3:
                self.wiadomosci.setText(self.zapytania[self.i])
                self.i += 1
            elif self.i == 3:
                self.stworz_komunikacje()
                self.i += 1
        else:
            message = self.pending

            header = struct.pack(f'!5s{len(self.odpowiedzi[2].encode("utf-8"))}s', "TEXT ".encode('utf-8'), self.odpowiedzi[2].encode("utf-8"))
          
            data = header + message.encode('utf-8')

            print(data)
            self.client_socket.send(len(header).to_bytes(4, byteorder='big'))
            self.client_socket.send(len(data).to_bytes(4, byteorder='big'))

            chunk_size = 1024
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                self.client_socket.send(chunk)

            # self.client_socket.send(header + data)

        self.text_input.clear()

    def wyslij_zdj(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Wybierz zdjęcie", "c:\\")
        with open(fname, 'rb') as f:
            image = f.read()

        header = struct.pack(f'!5s{len(self.odpowiedzi[2].encode("utf-8"))}s', "IMAGE".encode('utf-8'), self.odpowiedzi[2].encode("utf-8"))

        self.wiadomosci.show_image(image, reversed=True)

        self.client_socket.send(len(header).to_bytes(4, byteorder='big'))
        mess = header + image
        self.client_socket.send(len(mess).to_bytes(4, byteorder='big'))

        start = 0
        while start < len(mess):
            end = min(start + 1024, len(mess))
            self.client_socket.send(mess[start:end])
            start = end
        # self.client_socket.send(header + image)

    def send_username(self, server_socket, username):
        try:
            server_socket.send(username.encode('utf-8'))
        except Exception as e:
            print(f"Błąd wysyłania nazwy użytkownika do serwera: {e}")

    def stworz_komunikacje(self):
        print("aaaaaa")
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.odpowiedzi[0], int(self.odpowiedzi[1])))
            self.send_username(self.client_socket, self.odpowiedzi[2])

            print("storzono komunikacje")

            self.worker_thread = WorkerThread(self.client_socket, self.odpowiedzi[2])
            self.worker_thread.update_signal.connect(self.wiadomosci.check_type)
            self.worker_thread.start()
            # receive_thread = threading.Thread(target=self.receive_data_from_server, args=(self.client_socket,))
            # receive_thread.start()
        except Exception as e:
            print(f"Error creating communication: {e}")

    # def receive_data_from_server(self, server_socket):
    #     try:
    #         while True:
    #             data = server_socket.recv(1024).decode('utf-8')
    #             if not data:
    #                 break
    #             print(data)
    #
    #     except Exception as e:
    #         self.wiadomosci.setText(f"Błąd odbierania danych od serwera: {e}")
    #     finally:
    #         server_socket.close()


app = QApplication([])
widget = MojWidget()
widget.show()
sys.exit(app.exec())