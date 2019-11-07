import setuptools

from rs2wat import __version__

setuptools.setup(
    name="rs2wat",
    version=__version__,
    packages=setuptools.find_packages(),
    url="https://github.com/tuokri/rs2wat",
    author="tuokri",
    author_email="tuokri@tuta.io",
    description="Rising Storm 2: Vietnam WebAdmin Tools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
