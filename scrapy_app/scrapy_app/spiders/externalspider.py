# -*- coding: utf-8 -*-
'''
InfoSpider extracted from Botspider
Finds the title of index/home directory and ZIP Code, and name from impressum
'''
# import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class ExternalSpider(CrawlSpider):
    name = 'externalspider'

    def __init__(self, *args, **kwargs):
        self.url = kwargs.get('url')
        self.domain = kwargs.get('domain')
        self.keywords = kwargs.get('keywords')
        self.start_urls = [self.url]
        self.allowed_domains = [self.domain]
        self.pipelines = set([
            'external',
        ])

        ExternalSpider.rules = [
            Rule(LinkExtractor(unique=True, allow=()), callback='parse_item')
        ]
        super(ExternalSpider, self).__init__(*args, **kwargs)

    def parse_item(self, response):
        item = {}
        item['locals_url'] = response.url

        external_urls = LinkExtractor(allow=(), deny=self.allowed_domains,
                                      unique=True).extract_links(response)
        item['external_urls'] = set()

        for link in external_urls:
            item['external_urls'].add(link.url)
        self.logger.debug('external_urls found: %s' % len(external_urls))

        return item
