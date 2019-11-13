import setuptools

setuptools.setup(
    name="rs2wat",
    version="0.1.11",
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
    install_requires=[
        "Logbook>=1.5.3",
        "progressbar>=2.5",
        "psycopg2>=2.8.4",
        "python-dateutil>=2.8.1",
        "six>=1.13.0",
    ]
)
