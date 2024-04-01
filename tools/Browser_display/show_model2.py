import asyncio
import websockets

# Store the latest GLB file name received from the simulation
theGLBFile = 'default0.glb'  # Default value
theClients=set()

async def notifyClients():
    # Check if there are any connected clients
    if theClients:  
        await asyncio.wait([asyncio.create_task(aClient.send(theGLBFile)) for aClient in theClients])
        print("***Sent %s to all connected clients." % theGLBFile)

async def register(websocket):
    #Add the connecting browser client to the list
    if websocket not in theClients:
        print("***Registering client %s" % websocket)
        theClients.add(websocket)
    #print(theClients)
    #Push filename immediately on connect
    await notifyClients()  

async def unregister(websocket):
    #remove browser client to the list
    print("***Removing client %s" % websocket)
    theClients.remove(websocket)

async def handler(websocket, path):
    global theGLBFile
    await register(websocket)
    try:
        async for message in websocket:
            if message.startswith("simulation:"):
                theGLBFile = message.split(":", 1)[1]
                print("***Received new GLB file from simulation: %s" % theGLBFile)
                await notifyClients()
            else:
                await websocket.send(theGLBFile)
    finally:
        await unregister(websocket)

async def main():
    print("***Starting WebSocket server")
    async with websockets.serve(handler, "localhost", 5678):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())


# #!/usr/bin/env python

# import asyncio
# import websockets

# latest_glb_file = "default0.glb"  # Default value
# clients = set()  # Keep track of connected clients

# async def notify_clients():
#     if clients:  # Check if there are any connected clients
#         # Use asyncio.gather to run all send coroutines concurrently
#         await asyncio.gather(*(client.send(latest_glb_file) for client in clients))
#         print(f"Sent '{latest_glb_file}' to all connected clients.")

# async def register(websocket):
#     clients.add(websocket)
#     await notify_clients()  # Notify immediately on connect

# async def unregister(websocket):
#     clients.remove(websocket)

# async def handler(websocket, path):
#     global latest_glb_file
#     await register(websocket)
#     try:
#         async for message in websocket:
#             if message.startswith("simulation:"):
#                 _, new_glb_file = message.split(":", 1)
#                 latest_glb_file = new_glb_file
#                 print(f"Received new GLB file from simulation: {latest_glb_file}")
#                 await notify_clients()
#             else:
#                 await websocket.send(latest_glb_file)  # Send latest GLB file upon request
#     finally:
#         await unregister(websocket)

# async def main():
#     print("Starting WebSocket server")
#     async with websockets.serve(handler, "localhost", 5678):
#         await asyncio.Future()  # run forever

# if __name__ == "__main__":
#     asyncio.run(main())