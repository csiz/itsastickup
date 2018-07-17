
class ObservableClient:
  """Event based interaction via websockets (client).

  Connect to a server and subscribe to events. The client can then observe
  those events from the server. Conversely the client can trigger events
  on the server.

  The client needs to be asynchornously iterated on to receive items.
  """

  def __init__(self, address):
    pass

  async def trigger(self, event, data):
    pass

  async def subscribe(self, event):
    pass

  async def unsubscribe(self, event):
    pass

  async def __aiter__(self):
    pass


# async def pi_connection():
#   async with websockets.connect("ws://192.168.1.8:45223") as websocket:
#     await websocket.send(json.dumps(["subscribe", "measure"]))

#     async for message in websocket:
#       event, data = json.loads(message)
#       print(f"{event}: {data}")