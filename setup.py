# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='ffissh',
    version='0.1.dev1',

    url='https://github.com/tehasdf/ffissh',
    author='Matt Wheeler, Łukasz Maksymczuk',
    author_email='m@funkyhat.org',

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

    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        ],
    )
