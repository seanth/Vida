#!/usr/bin/env python

import asyncio
import datetime
import random
import websockets

async def sendGLB(websocket):
    fileList=['default0.glb','default1.glb','default2.glb','default3.glb']
    i=0
    while True:
        aFileName = random.choice(fileList)
        #aFileName = 'simulationOutput.glb'
        print("Sending model. Instance %i" % i)
        await websocket.send(aFileName)
        i=i+1
        await asyncio.sleep(5)

async def main():
    print("Starting async server")
    async with websockets.serve(sendGLB, "localhost", 5678):
        print("Awaiting request")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

