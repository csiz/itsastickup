import asyncio
import dataclasses
import typing
import logging
import traceback
import sys

from smbus2_asyncio import SMBus2Asyncio

from .. pi_scripts.gyro import Gyro
from .. pi_scripts.loop_runner import run_tasks
from . websocket_server import ObservableServer

async def main():
  print("Starting sensors.")
  smbus = SMBus2Asyncio(1)
  await smbus.open()

  gyro_0 = Gyro(smbus, AD0=False)
  await gyro_0.setup(sample_rate=50)


  print("Initializing server.")
  server = ObservableServer(host="0.0.0.0", port=45223)


  print("Starting tasks.")
  serve_forever = server.serve_forever()
  relay_gyro_0 = server.trigger_from("gyro-0-measure", gyro_0)


  # Run all tasks.
  try:
    await asyncio.gather(
      serve_forever,
      relay_gyro_0,
    )

  finally:
    print("Closing sensors.")
    # Put physical device to sleep.
    await gyro_0.close()


def print_exception(exc):
  return traceback.print_exception(type(exc), exc, exc.__traceback__)


if __name__ == "__main__":
  # Setup logging, and parse any arguments and pass them to main
  logging.basicConfig(level=logging.INFO)
  run_tasks(main())

