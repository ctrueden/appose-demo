import appose
from time import sleep

import appose
from appose.service import ResponseType

import numpy as np

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

show(ndarr.ndarray())
task.outputs["shape"] = ndarr.shape
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

    # Create a test image in shared memory.
    ndarr = appose.NDArray(dtype="float64", shape=[512, 384])
    narr = ndarr.ndarray()  # numpy.ndarray view on appose.NDArray
    # Fill the array with random values.
    # There's probably a slicker way without needing to slice/copy...
    ndarr.ndarray()[:] = np.random.random(ndarr.shape)

    # Actually do a real thing with napari: create and show an image.
    print("Showing image with napari...")
    task = python.task(napari_show, inputs={"ndarr": ndarr})

    task.wait_for()
    shape = task.outputs["shape"]
    print(f"Task complete! Got shape: {shape}")

print("Main program complete")
