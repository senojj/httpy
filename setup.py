from setuptools import setup, find_packages

setup(name='httpy',
      version='0.1.0',
      download_url='git@github.com:senojj/httpy.git',
      packages=find_packages(),
      author='Joshua Jones',
      author_email='joshua.jones.software@gmail.com',
      description='A simple HTTP client that uses only the Python standard library',
      long_description=open('README.md').read(),
      keywords='http client std',
      url='https://github.com/senojj/httpy',
      license='MIT')
