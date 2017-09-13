
from setuptools import setup


setup(
    name='ffissh',
    author='Matt Wheeler, Lukasz Maksymczuk',
    version='0.1',

    packages=[
        'ffissh',
        ],
    package_dir={'': 'src'},

    setup_requires=["cffi>=1.0.0,<2"],
    install_requires=[
        "cffi>=1.0.0,<2",
        ],
    cffi_modules=[
        "src/ffissh/_libssh2_build.py:ffibuilder",
        ],
    )
