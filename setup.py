from setuptools import setup

with open('requirements.txt') as handle:
    requirements = handle.readlines()

setup(
    name='artifax',
    version='0.0.1',
    description='python package for building artifacts from a computational graph',
    author='Bruno Lange',
    author_email='blangeram@gmail.com',
    url='https://gitlab.com/brunolange/artifax',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pylint'
        ]
    }
)
