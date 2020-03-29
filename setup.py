import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="boschshcpy",
    version="0.0.7",
    author="Clemens-Alexander Brust, Thomas Schamm",
    author_email="cabrust@pm.me, thomas@tschamm.de",
    description="Bosch Smart Home API Python Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tschamm/bosch-shc-py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=['requests==2.22']
)