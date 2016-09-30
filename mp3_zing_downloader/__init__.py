# coding=utf-8
import argparse
import os
import logging

import stagger

import requests
import scrapy.exceptions

import mp3_zing_downloader.crawler
import mp3_zing_downloader.spiders
import scrapy.settings
import scrapy.crawler

__author__ = 'tarzan'
# initialize logging
# configure_logging(install_root_handler=False)
# logging.basicConfig(
#     stream=sys.stderr,
#     format='%(levelname)s: %(message)s',
#     level=logging.INFO
# )
_logger = logging.getLogger(__name__)

DEST_DIRECTORY = None
FORCE_REDOWNLOAD = False

def _parse_arguments():
    """
    Configure and parse arguments from command line
    :rtype object
    """
    global DEST_DIRECTORY, FORCE_REDOWNLOAD

    parser = argparse.ArgumentParser()
    parser.add_argument('url',
                        help='The url to start downloading')
    parser.add_argument('--loglevel', default="INFO",
                        help="log level for the tool")
    parser.add_argument('-d', '--dir', default=os.getcwd(),
                        help="Directory to save songs")
    parser.add_argument('-f', "--force", default=False, action="store_true",
                        help="Force to redownload existing song")
    args = parser.parse_args()

    # set logger level
    loglevel = args.loglevel

    DEST_DIRECTORY = str(args.dir)
    DEST_DIRECTORY = os.path.expanduser(DEST_DIRECTORY)
    DEST_DIRECTORY = os.path.realpath(DEST_DIRECTORY)
    FORCE_REDOWNLOAD = args.force
    return args


class SongWriter(object):
    def __init__(self, item):
        genres = item['genres']
        name = item['name']
        artist = item['artist']
        artist_list = item['artist_list']
        album = item['album']
        resource_url = item['mp3_file_url']

        if not isinstance(genres, (list, tuple)):
            genres = [g.strip() for g in genres.split(',')]
        self.name = name
        self.artist = artist
        self.artist_list = artist_list
        self.album = album or ''
        self.genres = genres or []
        self.resource_url = resource_url

    def __str__(self):
        return "(%s) %s - %s #%s" % (
            self.album,
            self.name,
            self.artist,
            self.resource_url,
        )

    @property
    def abs_path(self):
        path = [DEST_DIRECTORY, self.artist]
        if self.album:
            path.append(self.album)
        path.append(self.name + ".mp3")
        return os.path.join(*path)

    @property
    def file_existed(self):
        return os.path.exists(self.abs_path)

    def write_metadata(self):
        print("\tRewriting metadata ...", end=' ')

        try:
            tag = stagger.read_tag(self.abs_path)
        except stagger.NoTagError:
            tag = stagger.default_tag()

        tag.title = self.name
        tag.album = self.album
        tag.album_artist = self.artist
        tag.artist = self.artist_list
        tag.genre = ', '.join(self.genres)
        tag.write(self.abs_path)
        print("\tDone")

    def write(self):
        print('Song detected: %s' % self)
        if self.file_existed:
            if not FORCE_REDOWNLOAD:
                print('\tSong existed => ignore')
                return
            else:
                print('\tSong existed => force redownload')

        print('\tStart downloading ...')
        mp3_data = requests.get(self.resource_url).content
        print("\tDone, %d bytes downloaded" % len(mp3_data))
        mp3_path = self.abs_path
        mp3_dir = os.path.dirname(mp3_path)
        print("\tSaving to %s ..." % mp3_path)

        if not os.path.exists(mp3_dir):
            os.makedirs(mp3_dir)
        with open(mp3_path, "wb") as f:
            f.write(mp3_data)
        print("\tDone, %d bytes were written" % os.path.getsize(mp3_path))

        self.write_metadata()


class SongItemPipeline(object):

    def __init__(self):
        self.count = 0

    def process_item(self, item, spider):
        writer = SongWriter(item)
        self.count += 1
        # print(self.count, writer)
        writer.write()


def main():
    args = _parse_arguments()
    _logger.setLevel(logging.INFO)
    url = args.url

    settings = scrapy.settings.Settings()
    process = scrapy.crawler.CrawlerProcess({
        'LOG_ENABLED': True,
        'LOG_LEVEL': 'WARNING',
        'ITEM_PIPELINES': {
            'mp3_zing_downloader.SongItemPipeline': 1,
        }
    })
    process.crawl(
        mp3_zing_downloader.spiders.Mp3ZingSpider,
        start_urls=[url, ]
    )
    process.start()

    print('Well done')
