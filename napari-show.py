import appose
from time import sleep

import appose
from appose.service import ResponseType

import numpy as np

# A script to start up the Qt application on the main thread.
# Would be nice to simplify this by calling napari.run() instead.
# I tried it and it didn't work -- TODO: troubleshoot why not.
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
task.export(main_task=task)  # Great idea? Or best idea ever?
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
    if 'viewer' not in globals() or not viewer:
        viewer = napari.Viewer()
        main_task.export(viewer=viewer)

    image_layer = viewer.add_image(narr)

    # Call back to the main process in response to actions in napari.
    # We use the main thread task, because this 'show' task will evaporate.
    # For this demo, we'll report mouse movement to the service process.

    def on_mouse_move(viewer, event):
        # event.position - coordinates in data space
        # event.pos - position in canvas coordinates
        # event.position - position in data/world coordinates
        # event.dims_displayed - which dimensions are currently displayed
        main_task.update(f"Mouse position -> {list(map(round, event.position))}")

    viewer.mouse_move_callbacks.append(on_mouse_move)

    main_task.update(f"Added image of shape {narr.shape} to viewer")

show(ndarr.ndarray())
task.outputs["shape"] = ndarr.shape  # This is dumb. Just for demo purposes.
"""

env = appose.base("/Users/curtis/.local/share/mamba/envs/napari").build()
with env.python() as python:
    # Print Appose events verbosely, for debugging purposes.
    #python.debug(print)

    # Start the Qt application event loop in the worker process.
    print("Starting Qt app event loop")
    setup = python.task(napari_setup, queue="main")
    ready = False
    def receive_update_from_napari_main_thread(event):
        if event.response_type != ResponseType.UPDATE:
            return

        global ready
        if not ready:
            print("Got initial update event! Marking Qt as ready")
            ready = True
            return

        # Subsequent update -- print out the message.
        print(event.message)

    setup.listen(receive_update_from_napari_main_thread)
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
    show_task = python.task(napari_show, inputs={"ndarr": ndarr})

    show_task.wait_for()
    shape = show_task.outputs["shape"]
    print(f"Task complete! Got shape: {shape}")

print("Main program complete")
