from setuptools import setup

with open('requirements.txt') as handle:
    requirements = handle.readlines()

setup(
    name='artifax',
    version='0.1.3',
    packages=['artifax'],
    description='python package for building artifacts from a computational graph',
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
