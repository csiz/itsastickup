import asyncio
import dataclasses
import typing
import logging
import traceback

from . pi_scripts import gyro
from . websocket_server import ObservableServer

def main():
  print("Starting sensors.")
  gyro_0 = gyro.Gyro()

  print("Initializing server.")
  server = ObservableServer(host="0.0.0.0", port=45223)


  print("Gather and run all tasks!")
  async def async_main():

    # We need to create these tasks within a running event loop.
    pending = [
      server.serve_forever(),
      server.trigger_from(gyro_0),
    ]

    # Run all pending tasks, loggint any exceptions.
    while pending:
      done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
      for task in done:
        try:
          await task
        except Exception as exc:
          print("Exception raised in running task!")
          print_exception(exc)

  try:
    # Sigh, no good way to gracefully exit on KeyboardInterrupt...
    asyncio.run(async_main(), debug=True)

  finally:
    print("Closing sensors.")
    # Finalize gyro thread and put physical device to sleep.
    gyro_0.close()


def print_exception(exc):
  return traceback.print_exception(type(exc), exc, exc.__traceback__)


if __name__ == "__main__":
  # Setup logging, and parse any arguments and pass them to main
  logging.basicConfig(level=logging.INFO)
  main()

