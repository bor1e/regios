# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class CrawlerSpider(CrawlSpider):
    name = 'crawler'

    def __init__(self, *args, **kwargs):
        # We are going to pass these args from our django view.
        # To make everything dynamic, we need to override them inside __init__ method
        self.url = kwargs.get('url')
        self.domain = kwargs.get('domain')
        self.start_urls = [self.url]
        self.allowed_domains = [self.domain]

        CrawlerSpider.rules = [
           Rule(LinkExtractor(unique=True), callback='parse_item'),
        ]
        super(CrawlerSpider, self).__init__(*args, **kwargs)

        '''
        rules = (
            Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
        )
        '''

    def parse_item(self, response):
        # You can tweak each crawled page here
        # Don't forget to return an object.
        i = {}
        i['url'] = response.url
        #i['domain_id'] = response.xpath('//input[@id="sid"]/@value').extract()
        #i['name'] = response.xpath('//div[@id="name"]').extract()
        #i['description'] = response.xpath('//div[@id="description"]').extract()
        return i