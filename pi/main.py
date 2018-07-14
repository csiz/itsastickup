import asyncio
import dataclasses
import json
import typing

import websockets

from pi_scripts import gyro



class WebSocketDispatcher:
  def __init__(self):
    # Dict from websocket to its subscriptions.
    self.connected = {}
    # Dict from subscription to subscribed websockets.
    self.subscriptions = {}


  async def connection(self, websocket, path):
    """Establish connection to client.
    * Keep track of `connected`.
    * Log connection and disconnect.
    * Initate `send` and `recv`.
    """
    # Add to active connections with no subscriptions yet.
    self.connected.setdefault(websocket, set())

    address, port = websocket.remote_address

    try:
      print(f"Connected to {address}:{port} at path {path}")

      await self._recv(websocket, path)

      # Gracious disconnect.
      disconnect_error = None

    except Exception as exc:
      disconnect_error = str(exc)
      raise

    finally:
      # Discard from active connections.
      socket_subscriptions = self.connected.pop(websocket)
      # Remove from all subscriptions.
      for sub in socket_subscriptions:
        self.subscriptions[sub].remove(websocket)


      maybe_error = "with error f{disconnect_error} " if disconnect_error else ""
      print(f"Disconnected {maybe_error} from {address}:{port} at path {path}")


  async def _recv(self, websocket, path):
    async for message in websocket:
      message = json.loads(message)


      action = message["action"]

      if action == "subscribe":
        self._subscribe(websocket, message["event"])
      elif action == "unsubscribe":
        self._unsubscribe(websocket, message["event"])
      else:
        raise ValueError(f"Unknown action {action}")



  def _subscribe(self, socket, event):
    # Add to subscriptions, and register it for this socket.
    self.subscriptions.setdefault(event, set()).add(socket)
    self.connected[socket].add(event)

  def _unsubscribe(self, socket, event):
    # Remove the socket from subscription.
    event_subscribers = self.subscriptions[event]
    event_subscribers.remove(socket)
    # Remove the whole event if no more subscribers.
    if not event_subscribers:
      self.subscriptions.pop(event)


  async def dispatch(self, messages):
    async for message in messages:

      event = message["event"]

      try:
        subscribed = self.subscriptions[event]

      except KeyError:
        # No subscriptions, then we have no-one to send to.
        pass

      else:
        # We have subscribers, yay :)

        # Encode the message.
        message = json.dumps(message)

        # Send to all sockets.
        for socket in subscribed:
          # Schedule the task and forget about it; we handle disconnects via `recv`.
          asyncio.get_event_loop().create_task(socket.send(message))





async def restructure_gyro_events(observable, name):
  """Restructure data events from gyro into `dict` messages.

  Need to handle:

    measure: Receives the latest Gyro.Measure from the gyro.
    exception: Exception that occured while reading the gyro.
    test_result: Test results from a gyro self test.
    start: Time when the sensor starts (or restarts after reset).
    discarded: Some measures were discared, because sensor overflow or range change.


  """

  async for event, args, kwargs in observable:
    # Check inputs are valid.
    assert not kwargs, "data event has no kwargs"
    assert len(args) <= 1, "data event has at most one args"

    # Add meta information, like what the event was and where it comes from.
    data = {"event": event, "source": name}

    if event == "measure":
      data.update(dataclasses.asdict(args[0]))
    elif event == "exception":
      data["error"] = str(args[0])
    elif event == "test_result":
      raise NotImplementedError
    elif event == "start":
      data["start"] = args[0]
    elif event == "discarded":
      data["discarded"] = True

    yield data




def main():
  gyro_0 = gyro.Gyro()

  websocket_dispatcher = WebSocketDispatcher()

  asyncio.get_event_loop().create_task(
    websocket_dispatcher.dispatch(
      restructure_gyro_events(gyro_0, "gyro_0")
    ))

  # Start server and serve until close.
  serve = websockets.serve(websocket_dispatcher.connection, "0.0.0.0", 45223)

  print("Starting to serve!")
  asyncio.get_event_loop().run_until_complete(serve)
  asyncio.get_event_loop().run_forever()
  print("Ending server!")

  # Finalize gyro thread and put physical device to sleep.
  gyro_0.close()

if __name__ == "__main__":
  # TODO: parse any arguments and pass them to main

  main()