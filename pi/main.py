import asyncio
import dataclasses
import typing
import logging
import traceback
import sys

from . pi_scripts import gyro
from . websocket_server import ObservableServer

def main():
  print("Starting sensors.")
  gyro_0 = gyro.Gyro()

  print("Initializing server.")
  server = ObservableServer(host="0.0.0.0", port=45223)


  print("Gather and run all tasks!")
  async def async_main():
    # Start all the tasks we need to run.
    serve_forever = asyncio.ensure_future(server.serve_forever())
    relay_gyro_0 = asyncio.ensure_future(server.trigger_from(gyro_0))

    def handle_input():
      command = sys.stdin.readline().strip()
      if command == "stop":
        print("Stopping!")
        server.stop()
        relay_gyro_0.cancel()
      else:
        print(f"Unknown command: {command}")

    # Run all pending tasks.
    tasks = [relay_gyro_0, serve_forever]
    try:
      asyncio.get_event_loop().add_reader(sys.stdin.fileno(), handle_input)
      await complete_all(tasks)
    finally:
      asyncio.get_event_loop().remove_reader(sys.stdin.fileno())


  try:
    # Sigh, no good way to gracefully exit on KeyboardInterrupt...
    asyncio.run(async_main())

  finally:
    print("Closing sensors.")
    # Finalize gyro thread and put physical device to sleep.
    gyro_0.close()


def print_exception(exc):
  return traceback.print_exception(type(exc), exc, exc.__traceback__)

async def complete_all(tasks):
  for task in asyncio.as_completed(tasks):
    try:
      await task
    except asyncio.CancelledError:
      pass

if __name__ == "__main__":
  # Setup logging, and parse any arguments and pass them to main
  logging.basicConfig(level=logging.INFO)
  main()

