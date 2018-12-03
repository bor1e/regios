# -*- coding: utf-8 -*-
''' 
Title Spider extracted from Botspider 
Finds the title of index/home directory
'''
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class TitleSpider(CrawlSpider):
    name = 'titlespider'

    def __init__(self, *args, **kwargs):
        self.url = kwargs.get('url')
        self.domain = kwargs.get('domain')
        self.keywords = kwargs.get('keywords')
        self.start_urls = [self.url]
        self.allowed_domains = [self.domain]
        self.pipelines = set([
            'title',
        ])

        TitleSpider.rules = [
            Rule(LinkExtractor(unique=True, allow=('/(?i)(home|index|index\.html)')), callback='parse_title'), # title rule
        ]
        super(TitleSpider, self).__init__(*args, **kwargs)

    def parse_title(self, response):
        item = {}
        item['title'] = response.xpath('//title/text()').extract_first()
        item['urls_checked'] = response.url
        self.logger.debug('TITLE FOUND %s' % item)
        return item
