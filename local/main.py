import websockets
import asyncio
import json


async def pi_connection():
  async with websockets.connect("ws://192.168.1.8:45223") as websocket:
    await websocket.send(json.dumps({"action": "subscribe", "event": "measure"}))

    async for message in websocket:
      message = json.loads(message)
      print(message)

def main():
  asyncio.get_event_loop().run_until_complete(pi_connection())



if __name__ == "__main__":
  # Parse command line args and pass them to main.
  main()