from setuptools import setup, find_packages
import os
import pathlib

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()


def versions_in_requirements(file):
    lines = file.read().splitlines()
    versions = [
        line
        for line in lines
        if not line.isspace() and "--" not in line
    ]
    return list(versions)


HERE = pathlib.Path(__file__).parent
with open(HERE / "requirements.txt") as f:
    required_list = versions_in_requirements(f)

setup(name='kusto_pandas',
      version='0.1.1',
      description='A wrapper around a Pandas DataFrame which allows you to use the syntax of the Kusto Query Language to transform the DataFrame',
      long_description = long_description,
      long_description_content_type='text/markdown',
      author='Jacob Stevenson',
      url='https://github.com/js850/KustoPandas',
      packages=find_packages(),
      install_requires=required_list,
     )