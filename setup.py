__author__ = 'tarzan'

from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

install_requires = [
    'stagger',
    'lxml',
    "requests >= 2.0",
]

setup(
    name='mp3_zing_downloader',
    version='1.1',
    author='Hoc .T Do',
    author_email='hoc3010@gmail.com',
    packages=['mp3_zing_downloader', ],
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