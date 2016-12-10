from setuptools import setup

setup(
    name="tamp",
    version="0.0.1",
    author="Greg Bowser",
    author_email="topnotcher@gmail.com",
    description=("A library for packing and unpacking binary structures."),
    license="GPL",
    keywords="structure pack unpack struct",
    url="https://github.com/topnotcher/tamp",
    packages=['tamp'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    extras_require={
        ":python_version<'3.4'": ["enum34"],
    },
)
