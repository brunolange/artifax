
from setuptools import setup
from os import path

with open('requirements.txt') as handle:
    requirements = handle.readlines()

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='artifax',
    version='0.1.3.1',
    packages=['artifax'],
    description='python package for building artifacts from a computational graph',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Bruno Lange',
    author_email='blangeram@gmail.com',
    url='https://gitlab.com/brunolange/artifax',
    install_requires=requirements,
    python_requires='>=3',
    extras_require={
        'dev': [
            'pylint'
        ]
    }
)
