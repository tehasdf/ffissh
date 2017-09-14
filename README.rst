libssh2 python wrapper
----------------------

Usage
=====

First, grab libssh2 and compile it, for example::

    git clone git@github.com:libssh2/libssh2.git
    cd libssh2
    mkdir build
    cd build
    cmake .. -DBUILD_SHARED_LIBS=ON
    cmake --build .

Now, you'll find the shared library in `libssh2/build/src/libssh2.so`.

Create a virtualenv and install cffi into it::

    virtualenv venv
    venv/bin/pip install cffi


Install ffissh::

    venv/bin/python -m pip install ../..


This will create the shared library `_libssh2_py.so`.

Now we can run the actual script, with LD_PRELOAD this time (need to figure out
a better way, but for now this is fine. Pass the path to the `cmake`'d shared library,
NOT the one made by `libssh2_build.py`)::


    LD_PRELOAD=/path/to/libssh2.so venv/bin/python run.py --host server.com --username user  ls

Woo.
