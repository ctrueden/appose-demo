import appose
from time import sleep

golden_ratio_in_python = """
# Approximate the golden ratio using the Fibonacci sequence.
previous = 0
current = 1
iterations = 50
for i in range(iterations):
    if task.cancel_requested:
        task.cancel()
        break
    task.update(current=i, maximum=iterations)
    v = current
    current += previous
    previous = v
task.outputs["numer"] = current
task.outputs["denom"] = previous
"""

env = appose.base("/Users/curtis/.local/share/mamba/envs/napari").build()
with env.python() as python:
    python.debug(print)
    task = python.task(golden_ratio_in_python)

    def task_listener(event):
        if event.response_type == ResponseType.UPDATE:
            print(f"Progress {task.current}/{task.maximum}")
        elif event.response_type == ResponseType.COMPLETION:
            numer = task.outputs["numer"]
            denom = task.outputs["denom"]
            ratio = numer / denom
            print(f"Task complete. Result: {numer}/{denom} =~ {ratio}");
        elif event.response_type == ResponseType.CANCELATION:
            print("Task canceled")
        elif event.response_type == ResponseType.FAILURE:
            print(f"Task failed: {task.error}")

    task.listen(task_listener)

    task.start()
    sleep(1)
    if not task.status.is_finished():
        # Task is taking too long; request a cancelation.
        task.cancel()

    task.wait_for()
