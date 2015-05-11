# coding=utf-8

__author__ = 'tarzan'

import collections
import argparse
from urllib import parse as urlparse
import requests
import stagger
# from stagger import id3
import lxml.html
import lxml.etree
import logging
import re
import os

HOST = "http://mp3.zing.vn"

DEST_DIRECTORY = os.getcwd()

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
        self.album = album or ''
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
        print("Rewriting metadata ...", end=' ')

        try:
            tag = stagger.read_tag(self.abs_path)
        except stagger.NoTagError:
            tag = stagger.default_tag()

        tag.title = self.name
        tag.album = self.album
        tag.album_artist = self.artist
        tag.artist = self.artist
        tag.genre = ', '.join(self.genres)
        tag.write(self.abs_path)
        print("Done")

    def __str__(self):
        return "(%s) %s - %s #%s" % (
            self.album,
            self.name,
            self.artist,
            self.resource_url,
        )


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

    DEST_DIRECTORY = str(args.dir)
    DEST_DIRECTORY = os.path.expanduser(DEST_DIRECTORY)
    DEST_DIRECTORY = os.path.realpath(DEST_DIRECTORY)
    return args


def _download_html_from_url(url):
    logger.info("Start downloading from url %s" % url)
    res = requests.get(url)
    html = res.text
    return html

_re_song_link = re.compile("(?:%s)?" % re.escape(HOST) + r"/bai-hat/[\w-]+/[\w-]+\.html")
_re_album_link = re.compile("(?:%s)?" % re.escape(HOST) + r"/album/[\w-]+/[\w-]+\.html")
_re_genre_link = re.compile("(?:%s)?" % re.escape(HOST) + r"/the-loai-bai-hat/[\w-]+/[\w-]+\.html")

def is_song_url(url):
    """
    Verify an url is a song or not?
    :param string url: url to verify
    :return bool:

    >>> is_song_url('/album/De-Nho-Mot-Thoi-Ta-Da-Yeu-Le-Quyen/ZWZ99880.html?st=6')
    False
    >>> is_song_url('/bai-hat/De-Nho-Mot-Thoi-Ta-Da-Yeu-Le-Quyen/ZWZBFB9C.html')
    True
    """
    return _re_song_link.match(url) is not None


def _find_songs(songs_url):
    """
    Find songs in html document
    :rtype list

    >>> songs = list(_find_songs(HOST + '/bai-hat/De-Nho-Mot-Thoi-Ta-Da-Yeu-Le-Quyen/ZWZBFB9C.html'))
    >>> type(songs)
    <class 'list'>
    >>> len(songs)
    1
    >>> songs = list(_find_songs(HOST + '/nghe-si/Le-Quyen/bai-hat'))
    >>> type(songs)
    <class 'list'>
    >>> len(songs)
    21
    """
    logger.info("Finding songs")

    crawled_urls = set([songs_url])
    queue = collections.deque([songs_url, ])
    yield songs_url

    while len(queue):
        songs_url = queue.popleft()

        # do not find song urls in song detail page
        # new in version 1.1
        if is_song_url(songs_url):
            continue
        html_doc = _download_html_from_url(songs_url)
        matches = _re_song_link.finditer(html_doc)
        urls = list(set([m.group() for m in matches]))
        logger.info("%d songs were found from %s" % (len(urls), songs_url))
        for url in urls:
            yield url
        tree = lxml.html.fromstring(html_doc)
        pages = tree.xpath("//div[contains(@class, 'pagination')]//ul/li/a")
        for a in pages:
            next_url = a.attrib.get('href', None)
            if not next_url:
                continue
            next_url = urlparse.urljoin(songs_url, next_url)
            if next_url not in crawled_urls:
                crawled_urls.add(next_url)
                queue.append(next_url)


_re_song_resource_xml = re.compile(
    "<embed[^>]+id=['\"]player['\"][^>]*flashvars=['\"][^'\"]*xmlURL=(.*?)[&'\"]",
    re.DOTALL | re.IGNORECASE)


def _fetch_song_info_from_url(url):
    """
    Download a song
    :type url: str

    >>> song = _fetch_song_info_from_url('/bai-hat/De-Nho-Mot-Thoi-Ta-Da-Yeu-Le-Quyen/ZWZBFB9C.html')
    >>> song.__str__()
    '(Để Nhớ Một Thời Ta Đã Yêu) Để Nhớ Một Thời Ta Đã Yêu - Lệ Quyên #http://mp3.zing.vn/xml/load-song/MjAxMSUyRjA1JTJGMjAlMkYyJTJGOSUyRjI5ZGUwNGIwNmY1OTVjMmZkMTYyNTE5NmQ2ODg4Y2ZkLm1wMyU3QzI='
    >>> song.genres
    ['Việt Nam', 'Nhạc Trẻ']
    """
    if not url.startswith("http"):
        url = HOST + '/' + url.lstrip("/")
    logger.info("Start fetching song information from url %s" % url)
    html_doc = requests.get(url).text
    tree = lxml.html.fromstring(html_doc)
    name = tree.xpath('//h1')
    if not len(name):
        logger.warn('Can not fetch song name from "%s"' % url)
        return None
    name = name[0]

    artist = name.xpath('//h1/following-sibling::*/h2/a')
    if not artist:
        logger.warn('Can not fetch song artist from "%s"' % url)
        return None
    artist = artist[0].text
    name = name.text

    song_info_els = tree.xpath("//div[contains(@class, 'info-content')]//a")
    if not len(song_info_els):
        logger.warn('Can not fetch song info from "%s"' % url)
        return None
    album = [a.text for a in song_info_els
             if _re_album_link.match(a.attrib.get('href', ''))]
    genres = [a.text for a in song_info_els
             if _re_genre_link.match(a.attrib.get('href', ''))]
    if len(album):
        album = album[0]
    else:
        album = None
    logger.debug('Album: %s' % album)
    logger.debug('Genres: %s' % genres)
    xml_url = _re_song_resource_xml.search(html_doc)
    if not xml_url:
        logger.warn("XML URL not found")
        return None

    xml_song_info = requests.get(xml_url.group(1)).text
    xml_tree = lxml.etree.fromstring(xml_song_info)

    song_url = xml_tree.xpath('//source')
    if not len(song_url):
        logger.warn('Can not get song URL from "%s"' % xml_url.group(1))
        return None
    song_url = song_url[0].text.strip('\r\n')
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
        print("%s already exists, ignore downloading" % mp3_path)
        return

    if not existed:
        print("Start downloading song %s ..." % song)
        mp3_data = requests.get(song.resource_url).content

        print("Done, %d bytes downloaded" % len(mp3_data))
        print("Saving to %s ..." % mp3_path)

        if not os.path.exists(mp3_dir):
            os.makedirs(mp3_dir)
        with open(mp3_path, "wb") as f:
            f.write(mp3_data)
        print("Done, %d bytes were written" % os.path.getsize(mp3_path))
    else:
        print("File existed, ignore downloading: %s" % mp3_path)
    song.write_metadata()


def main():
    args = _parse_arguments()
    logger.setLevel(logging.INFO)
    url = args.url
    if is_song_url(url):
        _fetch_song_info_from_url(url)
        return

    song_urls = _find_songs(url)
    for surl in song_urls:
        song = _fetch_song_info_from_url(surl)
        if song is None: continue;

        _download_song(song, args.force)

