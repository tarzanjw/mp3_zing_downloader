#coding=utf-8

__author__ = 'tarzan'

import collections
import argparse
import urlparse
from bs4 import BeautifulSoup
import requests
import logging
import re
import os
from mutagen.easyid3 import EasyID3
from mutagen import mp3, _id3frames

HOST = "http://mp3.zing.vn/"

DEST_DIRECTORY = os.getcwdu()

# initialize logging
logger = logging.getLogger(__name__)

log_handler = logging.StreamHandler()

# create formatter and add it to the handlers
# log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
# add the handlers to the logger
logger.addHandler(log_handler)

class Song(object):
    def __init__(self, name, artist, album, genres, resource_url):
        if not isinstance(genres, (list, tuple)):
            genres = [g.strip() for g in genres.split(',')]
        self.name = name
        self.artist = artist
        self.album = album or u''
        self.genres = genres or []
        self.resource_url = resource_url

    @property
    def abs_path(self):
        path = [DEST_DIRECTORY, self.artist]
        if self.album:
            path.append(self.album)
        path.append(self.name + ".mp3")
        return os.path.join(*path)

    def write_metadata(self):
        print "Rewriting metadata ...",
        audio = mp3.MP3(self.abs_path, ID3=EasyID3)
        audio["title"] = self.name
        audio["album"] = self.album
        audio["artist"] = self.artist
        audio.save()
        print "Done"

    def __unicode__(self):
        return u"(%s) %s - %s #%s" % (self.album, self.name, self.artist, unicode(self.resource_url))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

def _parse_arguments():
    """
    Configure and parse arguments from command line
    :rtype object
    """
    global DEST_DIRECTORY

    parser = argparse.ArgumentParser()
    parser.add_argument('url',
                   help='The url to start downloading')
    parser.add_argument('--loglevel', default="INFO",
                        help="log level for the tool")
    parser.add_argument('--dir', default=os.getcwd(),
                        help="Directory to save songs")
    parser.add_argument("--force", default=False, action="store_true",
                        help="Force to redownload existing song")

    args = parser.parse_args()

    # set logger level
    loglevel = args.loglevel
    if loglevel:
        loglevel = getattr(logging, loglevel.upper(), False)
        if loglevel:
            logger.setLevel(loglevel)
            log_handler.setLevel(loglevel)

    DEST_DIRECTORY = unicode(args.dir)
    DEST_DIRECTORY = os.path.expanduser(DEST_DIRECTORY)
    DEST_DIRECTORY = os.path.realpath(DEST_DIRECTORY)
    return args

def _download_html_from_url(url):
    logger.info("Start downloading from url %s" % url)
    res = requests.get(url)
    html = res.text
    return html

_re_song_link = re.compile(r"/bai-hat/[\w-]+/[\w-]+\.html")
def _find_songs(songs_url):
    """
    Find songs in html document
    :rtype list
    """
    logger.info("Finding songs")
    crawled_urls = set([songs_url])
    queue = collections.deque([songs_url,])
    while len(queue):
        songs_url = queue.popleft()
        html_doc = _download_html_from_url(songs_url)
        matches = _re_song_link.finditer(html_doc)
        urls = list(set([m.group() for m in matches]))
        logger.info("%d songs were found" % len(urls))
        print("%d songs were found from %s" % (len(urls), songs_url))
        for url in urls:
            yield url
        soup = BeautifulSoup(html_doc)
        pages = soup.find('ul', {'class': 'pagination'})
        for a in pages.find_all('a'):
            next_url = urlparse.urljoin(songs_url, a.get('href'))
            if next_url not in crawled_urls:
                crawled_urls.add(next_url)
                queue.append(next_url)
    # return urls

_re_song_resource_xml = re.compile("<embed[^>]+id=['\"]player['\"][^>]*flashvars=['\"][^'\"]*xmlURL=(.*?)[&'\"]",
                                   re.DOTALL | re.IGNORECASE)
def _fetch_song_info_from_url(url):
    """
    Download a song
    :type url: str
    """
    if not url.startswith("http"):
        url = HOST + url.lstrip("/")
    logger.info("Start fetching song information from url %s" % url)
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc)
    name = soup.find('h1')
    artist = name.find_next_sibling('h2')
    song_info = soup.find('p', {"class":"song-info"})
    album = [a for a in song_info.find_all('a')
             if a.get('href').startswith('/album')]
    genres = [a for a in song_info.find_all('a')
             if a.get('href').startswith('/the-loai-bai-hat')]
    if len(album):
        album = album[0]
    else:
        album = None
    xml_url = _re_song_resource_xml.search(html_doc)
    if not xml_url:
        logger.info("XML URL not found")
        return False
    if not name:
        logger.info("Song name not found")
        return False
    if not artist:
        logger.info("Song artist not found")
        return False

    xml_song_info = requests.get(xml_url.group(1)).text
    xml_soup = BeautifulSoup(xml_song_info, features="xml")
    song_url = xml_soup.find('source').text
    name = name.text
    artist = artist.text
    album = album.text if album else None
    genres = [g.text for g in genres] if genres else []
    song = Song(name, artist, album, genres, song_url)
    return song

def _download_song(song, force_redownload=False):
    """
    Download a song and save to hdd
    :type song: Song
    """
    mp3_path = song.abs_path
    mp3_dir = os.path.dirname(mp3_path)
    existed = os.path.exists(mp3_path)
    if existed and not force_redownload:
        print "%s already exists, ignore downloading" % mp3_path
        return

    if not existed:
        print "Start downloading song %s ..." % song,
        mp3_data = requests.get(song.resource_url).content
        print "Done, %d bytes downloaded" % len(mp3_data)
        print "Saving to %s ..." % mp3_path,

        if not os.path.exists(mp3_dir):
            os.makedirs(mp3_dir)
        with open(mp3_path, "w") as f:
            f.write(mp3_data)
        print "Done, %d bytes were written" % os.path.getsize(mp3_path)
    else:
        print "File existed, ignore downloading: %s" % mp3_path
    song.write_metadata()

def main():
    args = _parse_arguments()
    url = args.url
    if _re_song_link.match(url):
        _fetch_song_info_from_url(url)
        return

    song_urls = _find_songs(url)
    for surl in song_urls:
        song = _fetch_song_info_from_url(surl)
        _download_song(song, args.force)

