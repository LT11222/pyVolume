import asyncio
import functools
import websockets

from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

async def volume(websocket, path, volumeObj):
    
    while True:
        command = await websocket.recv()
        print(command)

        value = await websocket.recv()
        print(value)

        if command == "SET":
            volumeObj.SetMasterVolumeLevelScalar(float(value), None)

if __name__ == "__main__":

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volumeObj = cast(interface, POINTER(IAudioEndpointVolume))

    port = 6000
    start_server = websockets.serve(functools.partial(volume, volumeObj=volumeObj), '', port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()