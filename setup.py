from pathlib import Path
from setuptools import setup, find_packages

README = (Path(__file__).parent / "README.md").read_text()

setup(
    name='metabase-query-api',
    version='1.0.9',
    description='Metabase Query API with Retry and Bulk Param Values',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/tranngocminhhieu/metabase-query-api',
    author='Tran Ngoc Minh Hieu',
    author_email='tnmhieu@gmail.com',
    packages=find_packages(),
    install_requires=[
        'requests',
        'tenacity',
        'nest-asyncio'
    ]
)