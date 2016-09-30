# coding=utf-8
import json
import logging
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.linkextractors import LinkExtractor

__author__ = 'Tarzan'
_logger = logging.getLogger(__name__)


class Song(scrapy.Item):
    name = scrapy.Field()
    artist = scrapy.Field()
    artist_list = scrapy.Field()
    album = scrapy.Field()
    genres = scrapy.Field()
    info_url = scrapy.Field()
    mp3_file_url = scrapy.Field()


class Mp3ZingSpider(CrawlSpider):
    name = 'mp3.zing.vn'
    allowed_domains = ['mp3.zing.vn', ]

    rules = [
        # a song
        scrapy.spiders.Rule(
            LinkExtractor(
                allow=('/bai-hat/[\w-]+/[\w-]+\.html', ),
            ),
            callback='parse_song_info'
        ),
        # an artist
        scrapy.spiders.Rule(
            LinkExtractor(
                allow=('/nghe-si/[\w-]+/bai-hat', ),
            ),
            follow=True,
        ),
        # # a album
        # scrapy.spiders.Rule(
        #     LinkExtractor(
        #         allow=('/album/[\w-]+/[\w-]+\.html', ),
        #     ),
        #     follow=False,
        # ),
    ]

    def parse_song_info(self, res):
        """Parse a song info
        Args:
            res (scrapy.http.response.html.HtmlResponse): the reponse
        """
        def album(res):
            els = res.xpath('//h2/a[contains(@class, "txt-info")]/text()')
            if not els:
                return ''
            return els[0].extract().strip()

        item = Song()
        item['album'] = album(res)
        item['genres'] = [r.extract().strip() for r in
                          res.xpath(
                              '//a[contains(@class, "genre-track-log")]/text()')]
        item['info_url'] = res.xpath(
            "//div[@id='html5player']/@data-xml")[0].extract().strip()
        meta = {'item': item}
        return scrapy.Request(
            url=item['info_url'],
            callback=self.parse_song,
            meta=meta,
        )

    def parse_song(self, res):
        def get_mp3_url(quanlities, urls):
            for url in urls:
                if url:
                    break
            if not url:
                return None
            if not url.startswith('http'):
                url = 'http://' + url
            return url

        item = res.meta['item']

        info = json.loads(res.text)
        songdata = info['data'][0]
        item['name'] = songdata['name'].strip()
        item['artist'] = songdata['artist'].strip()
        artist_list = songdata.get('artist_list', [])
        item['artist_list'] = [a['name'].strip() for a in artist_list]
        if not item['artist_list']:
            item['artist_list'] = [item['artist'], ]
        item['mp3_file_url'] = get_mp3_url(songdata['qualities'],
                                           songdata['source_list'])
        return item
