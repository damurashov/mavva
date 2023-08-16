from setuptools import setup

with open("README.md", 'r') as description_file:
  long_description = description_file.read()

setup(
  name='mavva',
  packages=['mavva'],
  include_package_data=True,
  version='0.1.1',
  license='MIT',
  description='An extendable MAVLink framework working straight out-of-the-box. I use it, maybe you will too',
  long_description_content_type="text/markdown",
  long_description=long_description,
  setup_requires=['wheel'],
  install_requires=[
          'pymavlink==2.4.37',
          'pyserial==3.5',
      ],
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  python_requires='>=3.7',
)
