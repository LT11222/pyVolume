import asyncio
import websockets
import time
import threading
import queue

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider, QLabel, QSizePolicy)

async def sendCommand(websocket, command, value):
    await websocket.send(str(command))
    await websocket.send(str(value))

async def sendLoop(websocket, dataOutQueue, killEvent):
    while True and not killEvent.is_set():
        try:
            item = dataOutQueue.get_nowait()
            print(item)
            await sendCommand(websocket, item[0], item[1])
            dataOutQueue.task_done()
        except:
            pass
        await asyncio.sleep(0.001)
    return

async def recvLoop(websocket, dataInQueue, killEvent):
    while True and not killEvent.is_set():
        res = await websocket.recv()
        dataInQueue.put_nowait(res)

async def volumeHandler(loop, dataOutQueue, dataInQueue, killEvent):
        uri = "ws://localhost:6000"
        async with websockets.connect(uri) as websocket:
            await asyncio.create_task(sendLoop(websocket, dataOutQueue, killEvent))
            await asyncio.create_task(recvLoop(websocket, dataInQueue, killEvent))
        loop.stop()
        return

def volumeThread(dataOutQueue, dataInQueue, killEvent):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(volumeHandler(loop, dataOutQueue, dataInQueue, killEvent))
    loop.run_forever()
    return

class mainWindow(QWidget):
    def __init__(self, dataOutQueue):
        super(mainWindow, self).__init__()

        self.dataOutQueue = dataOutQueue

        self.volume = 0
        self.mute = 0

        layout = QGridLayout()

        volDownBtn = QPushButton("Down")
        volUpBtn = QPushButton("Up")
        self.volSlider = QSlider(Qt.Vertical)
        self.volLabel = QLabel(str(self.volume))

        volDownBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        volUpBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        volDownBtn.clicked.connect(self.volDown)
        volUpBtn.clicked.connect(self.volUp)

        self.volSlider.valueChanged.connect(self.setVol)

        self.volSlider.setMinimum(0)
        self.volSlider.setMaximum(100)

        self.volLabel.setAlignment(Qt.AlignCenter)        

        layout.addWidget(self.volLabel, 0, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.volSlider, 1, 0, 3, 1, alignment=Qt.AlignCenter)
        layout.addWidget(volUpBtn, 0, 3, 2, 1)
        layout.addWidget(volDownBtn, 2, 3, 2, 1)

        layout.setColumnMinimumWidth(0, 100)

        self.setLayout(layout)
        self.show()

    def update(self):
        self.volLabel.setText(str(self.volume))
        self.volSlider.valueChanged.disconnect()
        self.volSlider.setValue(self.volume)
        self.volSlider.valueChanged.connect(self.setVol)
        self.dataOutQueue.put(("SET", self.volume/100.0))

    def setVol(self, value):
        self.volume = value
        self.update()

    def volDown(self):
        self.volume -= 2
        if self.volume < 0:
            self.volume = 0
        self.update()

    def volUp(self):
        self.volume += 2
        if self.volume > 100:
            self.volume = 100
        self.update()
        
if __name__ == "__main__":
    try:
        dataOutQueue = queue.Queue()
        dataInQueue = queue.Queue()
        killEvent = threading.Event()
        
        socketThread = threading.Thread(target=volumeThread, args=((dataOutQueue, dataInQueue, killEvent)))
        socketThread.start()

        app = QApplication([])
        window = mainWindow(dataOutQueue)

        try:
            app.exec_()
        except Exception as e:
            killEvent.set()
            print(e)

    except Exception as e:
        killEvent.set()
        print(e)

    killEvent.set()