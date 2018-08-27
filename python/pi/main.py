import asyncio
import dataclasses
import typing
import logging
import traceback
import sys
from time import monotonic

from smbus2_asyncio import SMBus2Asyncio

from .. pi_scripts.gyro import Gyro
from .. pi_scripts.servo import Servo
from .. pi_scripts.loop_runner import run_tasks
from . websocket_server import ObservableServer

async def main(commands):
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

  async def release_servos(*argv):
    await servos.release_all()
  commands["release"] = release_servos
  commands["off"] = release_servos


  print("Initializing server.")
  server = ObservableServer(host="0.0.0.0", port=45223)

  print("Starting tasks.")
  serve_forever = server.serve_forever()
  relay_gyro_0 = server.trigger_from("gyro-0-measure", gyro_0)
  control, echo_controls = control_forever(server, servos)
  beat = heartbeat(server)

  # Run all tasks.
  try:
    await asyncio.gather(
      serve_forever,
      relay_gyro_0,
      control,
      echo_controls,
      beat,
    )

  finally:
    print("Closing sensors.")
    # Put physical device to sleep.
    await gyro_0.close()
    print("Releasing servos.")
    await servos.release_all()


async def heartbeat(server):
  while True:
    await server.trigger("time", monotonic())
    await asyncio.sleep(0.1)

def control_forever(server, servos):
  # Use a queue so the event loop can drive the controller and the server
  # independently. We don't want a slow send to pause processing commands.
  actions = asyncio.Queue()

  async def control():

    sticky_servos = {}

    async for event, data in server:

      if event == "move-servo":
        n = data["n"]
        position = data["position"]

        # Check if we want this servo to stick to this position for some time.
        if "sticky" in data:
          sticky_until = monotonic() + data["sticky"]
          sticky_servos[n] = sticky_until

        # Check if the servo is sticky.
        elif n in sticky_servos:
          sticky_until = sticky_servos[n]
          # Still in sticky period, ignore command.
          if monotonic() < sticky_until:
            continue
          else:
            sticky_servos.pop(n)

        await servos.drive(n=n, position=position)

        await actions.put(("servo-position", {
          "n": n,
          "position": position,
          "time": monotonic(),
        }))


  async def echo_controls():
    while True:
      device, data = await actions.get()
      await server.trigger(device, data)

  return control(), echo_controls()



def print_exception(exc):
  return traceback.print_exception(type(exc), exc, exc.__traceback__)


if __name__ == "__main__":
  # Setup logging, and parse any arguments and pass them to main
  logging.basicConfig(level=logging.INFO)
  # Initialize empty commands, but allow adding them from the main function.
  commands = {}
  # TODO: maybe there's a better way for this? Do we need a class?
  run_tasks(main(commands), commands=commands)

