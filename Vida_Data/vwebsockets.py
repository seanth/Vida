import asyncio
import websockets


async def send3dFileName(uri, aFileName):
    async with websockets.connect(uri) as websocket:
        await websocket.send(f"simulation:{aFileName}")
        print("Sent new GLB file to server: %s" % aFileName)