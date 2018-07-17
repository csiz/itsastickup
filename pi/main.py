import asyncio
import dataclasses
import typing
import logging
import traceback

from . pi_scripts import gyro
from . websocket_server import ObservableServer

def print_exception(exc):
  return traceback.print_exception(type(exc), exc, exc.__traceback__)

async def main(loop):
  print("Starting sensors.")
  gyro_0 = gyro.Gyro()

  print("Initializing server.")
  server = ObservableServer(host="0.0.0.0", port=45223)

  try:
    # Start up server task.
    server_task = loop.create_task(server.serve_forever())

    # Start data tasks.
    pending = list(map(loop.create_task, [
      server.trigger_from(gyro_0),
    ]))

    # Wait for all data task to complete; when they're all done we cna safely
    # shutdown the server as there's nothing else to do...
    while pending:

      # Grab tasks as they complete and do any necessary error handling.
      done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

      # Check whether all completed tasks completed gracefully.
      for task in done:
        try:
          await task
        except Exception as exc:
          print("Unhandled exception from task:")
          print_exception(exc)

  except asyncio.CancelledError:
    # Absorb a CancelledError and try to exit gracefully.
    print("Exiting after cancelation...")


  # Cleanup
  # -------

  finally:

    # Wait for all pending tasks to finish in case the main task was cancelled.
    if pending:
      print("Cancelling unfinished tasks...")
      unfinished_tasks = asyncio.gather(*pending, return_exceptions=True)
      unfinished_tasks.cancel()
      task_results = await unfinished_tasks
      for result in task_results:
        if isinstance(result, Exception):
          print("Exception while cancelling unfinished tasks:")
          print_exception(result)

    print("Stopping the server...")
    server.stop()
    await server_task

    print("Closing sensors...")
    # Finalize gyro thread and put physical device to sleep.
    gyro_0.close()


    print("Cleanup complete; stopping event loop.")
    loop.stop()

if __name__ == "__main__":
  # Parse any arguments and pass them to main


  # Run the main task in an event loop.
  logging.basicConfig(level=logging.INFO)

  loop = asyncio.get_event_loop()
  loop.set_debug(True)

  main_task = loop.create_task(main(loop))

  try:
    loop.run_forever()
  except KeyboardInterrupt:
    print("User interrupt; cancelling main task...")
    main_task.cancel()
    try:
      loop.run_forever()
    except Exception as exc:
      print(f"Unhandled exception during task cancelling: {exc}")
  finally:
    print("Closing event loop.")
    loop.close()

    # Holy mother of error handling!
