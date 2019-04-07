# -*- coding: utf-8 -*-
'''
InfoSpider extracted from Botspider
Finds the title of index/home directory and ZIP Code, and name from impressum
'''
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from start.models import Domains


class ExternalSpider(CrawlSpider):
    name = 'externalspider'

    def __init__(self, *args, **kwargs):
        self.started_by_domain = kwargs.get('started_by_domain')
        self.allowed_domains = [self.started_by_domain]
        obj = Domains.objects.get(domain=self.started_by_domain)
        # self.start_urls = ['http://' + x for x in self.allowed_domains]
        self.start_urls = [obj.cleaned_url]
        self.keywords = kwargs.get('keywords')

        ExternalSpider.rules = [
            Rule(LinkExtractor(unique=True),
                 callback='parse_item')
        ]
        super(ExternalSpider, self).__init__(*args, **kwargs)

    def parse_item(self, response):
        item = {}
        item['locals_url'] = response.url
        item['external_urls'] = set()

        external_urls = LinkExtractor(allow=(), deny=self.allowed_domains,
                                      unique=True).extract_links(response)

        for link in external_urls:
            item['external_urls'].add(link.url)

        return item
