# type: ignore

import setuptools

with open('VERSION', 'r') as f:
    version = f.read()

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="gean",
    version=version,
    author="Gabriel Garcia",
    author_email="me@garciat.com",
    description="A minimal IOC container inspired by Spring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/garciat/gean",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov', 'pytest-mypy'],
)
