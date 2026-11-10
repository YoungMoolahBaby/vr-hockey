"""Import this before xr or OpenGL (importing xr loads PyOpenGL, which reads it then): PyOpenGL's
error checking off. With it on, every GL call is followed by a glGetError, and each of those makes
the CPU wait for the driver to catch up: in the headset, time out of every frame. Set
PYOPENGL_ERROR_CHECKING=1 to have it back while debugging."""

import os

os.environ.setdefault("PYOPENGL_ERROR_CHECKING", "0")
