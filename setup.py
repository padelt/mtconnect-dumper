from setuptools import setup, find_packages

import sys
if sys.version_info[0] < 3:
        sys.exit("Sorry, Python 2 is not supported. Please install with "
                "Python 3! "+repr(sys.version_info))

setup(
    name='mtconnect-dumper',
    version='1.1.4',
    packages=find_packages(),
    install_requires=[
        'Click',
        'Click-log',
        'lxml',
        'requests',
    ],
    entry_points='''
        [console_scripts]
        mtconnect_dumper=mtconnect_dumper.mtconnect_dumper:dump
    ''',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3 :: Only",
    ],
)

