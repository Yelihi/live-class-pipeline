import threading

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib  # noqa: E402

_loop: GLib.MainLoop | None = None
_thread: threading.Thread | None = None


def start():
    global _loop, _thread
    if _thread and _thread.is_alive():
        return
    _loop = GLib.MainLoop()
    _thread = threading.Thread(target=_loop.run, daemon=True)
    _thread.start()


def stop():
    global _loop
    if _loop:
        _loop.quit()
        _loop = None
