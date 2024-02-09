#!/usr/bin/env python

import asyncio
import datetime
import random
import websockets

async def show_time(websocket):
    fileList=['default0.glb','default3.glb']
    while True:
        aFileName = random.choice(fileList)
        with open(aFileName, 'rb') as theFile:
            modelData = theFile.read()
        await websocket.send(modelData)
        await asyncio.sleep(5)

async def main():
    async with websockets.serve(show_time, "localhost", 5678):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())