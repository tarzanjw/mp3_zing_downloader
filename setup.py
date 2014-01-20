__author__ = 'tarzan'

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

install_requires = [
    "BeautifulSoup4",
    "requests >= 2.0",
    "BeautifulSoup4",
]

setup(
    name='mp3_zing_downloader',
    version='0.1.7',
    author='Hoc .T Do',
    author_email='hoc3010@gmail.com',
    packages=find_packages(),
    scripts=[],
    url='https://github.com/tarzanjw/mp3_zing_downloader',
    license='LICENSE',
    description='Downloader to download music from mp3.zing.vn',
    long_description=README + "\n\n" + CHANGES,
    install_requires=install_requires,
      entry_points="""\
      [console_scripts]
      mp3zingdownload = mp3_zing_downloader:main
      """,
)