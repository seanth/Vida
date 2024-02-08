#!/usr/bin/env python

import asyncio
import datetime
import random
import websockets

async def show_time(websocket):
    fileList=['default0.glb','default1.glb','default2.glb','default3.glb']
    while True:
        # message = datetime.datetime.utcnow().isoformat() + "Z"
        # message = "default0.glb"
        message = random.choice(fileList)
        await websocket.send(message)
        await asyncio.sleep(random.random() * 2 + 1)

async def main():
    async with websockets.serve(show_time, "localhost", 5678):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())