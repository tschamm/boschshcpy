from setuptools import find_packages, setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="boschshcpy",
    version="0.2.53",
    url="https://github.com/tschamm/boschshcpy",
    author="Clemens-Alexander Brust, Thomas Schamm",
    author_email="cabrust@pm.me, thomas@tschamm.de",
    description="Bosch Smart Home Controller API Python Library",
    keywords="boschshcpy",
    license="bsd-3-clause",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "boschshc_rawscan=boschshcpy.rawscan:main",
            "boschshc_registerclient=boschshcpy.register_client:main",
        ],
    },
    package_data={"": ["tls_ca_chain.pem"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
    ],
    python_requires=">=3.10, <4",
    install_requires=[
        "cryptography>=3.3.2",
        "getmac>=0.8.2,<1",
        "requests>=2.22",
        "zeroconf>=0.28.0",
    ],
    project_urls={
        "Bug Reports": "https://github.com/tschamm/boschshcpy/issues",
        "Source": "https://github.com/tschamm/boschshcpy",
    },
    include_package_data=True,
)
