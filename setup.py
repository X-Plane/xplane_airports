from setuptools import setup, find_packages

with open('README.md') as f:
    readme_md = f.read()

setup(
    name='xplane_airports',
    version='3.2.1',
    packages=find_packages(),
    url='https://github.com/X-Plane/xplane_airports',
    license='MIT',
    author='Tyler Young',
    author_email='tyler@x-plane.com',
    python_requires='>=3.6',  # For dataclasses
    description='Tools for manipulating X-Plane\'s apt.dat files & interfacing with the X-Plane Scenery Gateway',
    long_description=readme_md,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Games/Entertainment :: Simulation",
    ],
    install_requires=[
        'requests',
        'dataclasses>=0.6; python_version < "3.7"'
    ],
    test_suite='xplane_airports/test_AptDat.py'
)
