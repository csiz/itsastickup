import asyncio
import logging
import dataclasses
import json

import websockets


class ObservableServer:
  """Event based interaction via websockets (server).

  Events are dispatched to all subscribed clients. Conversely events can be
  observerd from all connected clients. Internally handled subscribe events
  that control which events are transmitted over the wire to the clients.

  Subscribe events:
    subscribe: Subscribes the client to the specified `event`.
    unsubscribe: Unsubscribes the client from the `event`, events will no
      longer be transmitted to the client.
  """
  def __init__(self, host, port):
    self.host = host
    self.port = port

    # Dict from websocket to its subscriptions.
    self.connected = {}
    # Dict from subscription to subscribed websockets.
    self.subscriptions = {}


  async def trigger(self, event, data):
    """Dispatch `event` to all subscribed clients."""

    subscribed = self.subscriptions.get(event)
    if not subscribed:
      # No subscriptions, then save the work of serializing the event.
      return

    # We have subscribers, yay :)

    # Encode the message.
    message = json.dumps((event, asprimitives(data)))

    # Send to all subscribed clients.
    done, _ = await asyncio.wait(
      [websocket.send(message) for websocket in subscribed],
      return_when=asyncio.ALL_COMPLETED)

    # Check that sending was succesful.
    for sent in done:
      try:
        await sent
      # Ignore closed connections as the `recv` side will deal with them.
      except websockets.ConnectionClosed:
        pass


  async def trigger_from(self, async_event_source):
    """Continuously dispatch events from an asynchornous generator."""
    async for event, data in async_event_source:
      await self.trigger(event, data)


  async def __iter__(self):
    while not self._stop_event.is_set():
      event_tuple = await self._pending_events.get()
      yield event_tuple


  async def serve_forever(self):
    """Run the websocket message server forever, or until `stop`."""

    # Event used to stop the server; see the `stop` method.
    self._stop_event = asyncio.Event()

    # Events received, waiting to be processed.
    self._pending_events = asyncio.Queue()

    async with websockets.serve(self._connection, self.host, self.port):
      try:
        # Wait for the stop command.
        await self._stop_event.wait()
      except (KeyboardInterrupt, asyncio.CancelledError):
        # Exit gracefully on cancel.
        logging.info("serve_forever() got interrupted instead of stop()")
        raise
      finally:
        # Ensure the stop event was set in case we're exiting due to an error.
        self._stop_event.set()


  async def _connection(self, websocket, path):
    """Establish connection to client."""
        # Add to active connections with no subscriptions yet.
    self.connected.setdefault(websocket, set())

    address, port = websocket.remote_address

    try:
      # Connect and start receinving events.
      logging.info(f"Connected to {address}:{port} at path {path}")

      await self._recv(websocket, path)

    except (KeyboardInterrupt, asyncio.CancelledError):
      # Connection is a floating task, if an interrupt pops up here, we should
      # close the server down.
      logging.info("_connection() got interrupted; stopping server")
      self.stop()
      raise

    except Exception as exc:
      # Suppress connection errors.
      logging.error(f"Disconnecting with unhandled exception: {exc}")

    finally:
      # Discard from active connections.
      socket_subscriptions = self.connected.pop(websocket)
      # Remove from all subscriptions.
      for sub in socket_subscriptions:
        self.subscriptions[sub].remove(websocket)

      logging.info(f"Disconnected from {address}:{port} at path {path}")


  async def _recv(self, websocket, path):
    """Continuously receive events from client until disconnect."""

    async for message in websocket:

      event, data = json.loads(message)

      if event == "subscribe":
        self._subscribe(websocket, data)
      elif event == "unsubscribe":
        self._unsubscribe(websocket, data)
      else:
        await self._pending_events.put((event, data))


  def _subscribe(self, websocket, event):
    """Subscribe client to this `event` type."""

    # Add to subscriptions, and register it for this socket.
    self.subscriptions.setdefault(event, set()).add(websocket)
    self.connected[websocket].add(event)

  def _unsubscribe(self, websocket, event):
    """Unsubscribe client from these `event` type."""

    # Remove the socket from subscription.
    event_subscribers = self.subscriptions[event]
    event_subscribers.remove(websocket)
    # Remove the whole event if no more subscribers.
    if not event_subscribers:
      self.subscriptions.pop(event)


  def stop(self):
    """Stop from serving forever."""
    self._stop_event.set()


def asprimitives(data):
  """Convert an arbitrary object to a json serializable type."""
  if data is None:
    return data

  if isinstance(data, (bool, int, float, str)):
    return data

  if dataclasses.is_dataclass(data):
    return dataclasses.asdict(data)

  if isinstance(data, list):
    return [asprimitives(d) for d in data]

  if isinstance(data, dict):
    return {k: asprimitives(v) for k, v in data.items()}

  raise ValueError(f"asprimitives() unable to convert {type(data)} to primitive")

