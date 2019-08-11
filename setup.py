from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "rasa==1.2.1",
    "typing==3.6.2",
    "rasa_sdk==1.1.1",
    "ruamel.base==1.0.0"
]

setup(
    name='rasa_denerator',
    install_requires=install_requires,
    packages=find_packages(),
    version='1.0.0',
    description='A simple way of generating a domain.yml file for Rasa',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Collen-Roller/Rasa-Denerator",
    author='Collen Roller',
    entry_points={
          'console_scripts': [
              'rasa_denerator = rasa_denerator.__main__:main'
          ]
      },
    author_email='collen.roller@gmail.com',
    keywords=['rasa', 'rasa_core', 'rasa_nlu'],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)