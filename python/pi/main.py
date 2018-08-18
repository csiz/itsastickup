import asyncio
import dataclasses
import typing
import logging
import traceback
import sys

from smbus2_asyncio import SMBus2Asyncio

from .. pi_scripts.gyro import Gyro
from .. pi_scripts.servo import Servo
from .. pi_scripts.loop_runner import run_tasks
from . websocket_server import ObservableServer

async def main():
  print("Starting sensors.")
  smbus = SMBus2Asyncio(1)
  await smbus.open()

  # Initialize gyro at a rather reduced sample rate.
  gyro_0 = Gyro(smbus, AD0=False)
  await gyro_0.setup(sample_rate=50)

  # Initialize servos and set the limits to what my cheap servos seem to have.
  servos = Servo(smbus)
  await servos.setup(modulation_rate=50)
  servos.low_limit = 0.6
  servos.high_limit = 2.6


  print("Initializing server.")
  server = ObservableServer(host="0.0.0.0", port=45223)

  print("Starting tasks.")
  serve_forever = server.serve_forever()
  relay_gyro_0 = server.trigger_from("gyro-0-measure", gyro_0)
  control = control_forever(server, servos)



  # Run all tasks.
  try:
    await asyncio.gather(
      serve_forever,
      relay_gyro_0,
      control,
    )

  finally:
    print("Closing sensors.")
    # Put physical device to sleep.
    await gyro_0.close()



async def control_forever(server, servos):
  async for event, data in server:
    if event == "move-servo":
      await servos.drive(n=data["n"], position=data["position"])


def print_exception(exc):
  return traceback.print_exception(type(exc), exc, exc.__traceback__)


if __name__ == "__main__":
  # Setup logging, and parse any arguments and pass them to main
  logging.basicConfig(level=logging.INFO)
  run_tasks(main())

