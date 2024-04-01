import asyncio
import websockets
import random

async def sendGLBFile(uri, aFileName):
    async with websockets.connect(uri) as websocket:
        await websocket.send(f"simulation:{aFileName}")
        print(f"Sent new GLB file to server: {aFileName}")

# Example usage
uri = "ws://localhost:5678/"
fileList=['untitled_folder/default0.glb','untitled_folder/default1.glb','untitled_folder/default2.glb','untitled_folder/default3.glb']
aFileName = random.choice(fileList)
asyncio.run(sendGLBFile(uri, aFileName))