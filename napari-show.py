import appose
from time import sleep

import appose
from appose.service import ResponseType

napari_setup = """
# CRITICAL: Qt must run on main thread on macOS.

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QTimer
import threading
import sys

# Configure Qt for macOS before any QApplication creation
QApplication.setAttribute(Qt.AA_MacPluginApplication, True)
QApplication.setAttribute(Qt.AA_PluginApplication, True)
QApplication.setAttribute(Qt.AA_DisableSessionManager, True)

# Create QApplication on main thread.
qt_app = QApplication(sys.argv)

# Prevent Qt from quitting when last Qt window closes; we want napari to stay running.
qt_app.setQuitOnLastWindowClosed(False)

task.export(qt_app=qt_app)
task.update()

# Run Qt event loop on main thread.
qt_app.exec()
"""

napari_shutdown = """
# Signal main thread to quit.
qt_app.quit()
"""

napari_show = """
import napari
import numpy as np

from superqt import ensure_main_thread

@ensure_main_thread
def show(narr):
    napari.imshow(narr)

narr = np.random.random([512, 384])
show(narr)
task.outputs["shape"] = narr.shape
"""

env = appose.base("/Users/curtis/.local/share/mamba/envs/napari").build()
with env.python() as python:
    # Print Appose events verbosely, for debugging purposes.
    python.debug(print)

    # Start the Qt application event loop in the worker process.
    print("Starting Qt app event loop")
    setup = python.task(napari_setup, queue="main")
    ready = False
    def check_ready(event):
        if event.response_type == ResponseType.UPDATE:
            print("Got update event! Marking Qt as ready")
            global ready
            ready = True
    setup.listen(check_ready)
    setup.start()
    print("Waiting for Qt startup...")
    while not ready:
        sleep(0.1)
    print("Qt is ready!")

    # Actually do a real thing with napari: create and show an image.
    print("Showing image with napari...")
    task = python.task(napari_show)

    #def task_listener(event):
    #    if event.response_type == ResponseType.UPDATE:
    #        print(f"Progress {task.current}/{task.maximum}")
    #    elif event.response_type == ResponseType.COMPLETION:
    #        numer = task.outputs["numer"]
    #        denom = task.outputs["denom"]
    #        ratio = numer / denom
    #        print(f"Task complete. Result: {numer}/{denom} =~ {ratio}");
    #    elif event.response_type == ResponseType.CANCELATION:
    #        print("Task canceled")
    #    elif event.response_type == ResponseType.FAILURE:
    #        print(f"Task failed: {task.error}")

    #task.listen(task_listener)

    task.wait_for()
    shape = task.outputs["shape"]
    print(f"Task complete! Got shape: {shape}")

print("Main program complete")
