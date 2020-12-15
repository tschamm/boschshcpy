from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="boschshcpy",
    version="0.1.18.dev4",
    url="https://github.com/tschamm/boschshcpy",
    author="Clemens-Alexander Brust, Thomas Schamm",
    author_email="cabrust@pm.me, thomas@tschamm.de",
    description="Bosch Smart Home Controller API Python Library",
    license='bsd-3-clause',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "License :: OSI Approved :: BSD License"
    ],
    platform='any',
    python_requires='>=3.7',
    install_requires=['requests>=2.22', 'zeroconf>=0.28.0', 'getmac==0.8.2']
)
