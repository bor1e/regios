# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse

'''
if the pages you want to crawl change on a regular basis you could create 
a spider that crawls the sitemap, divides the links up into n chunks,
then starts n other spiders to actually crawl the site.
# https://stackoverflow.com/questions/23047080/sharing-visited-urls-between-multiple-spiders-in-scrapy
'''


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
            Rule(LinkExtractor(allow=('/(?i)impressum')), callback='parse_impressum'),
            Rule(LinkExtractor(unique=True), callback='parse_item'),
            #test_ Rule(LinkExtractor(unique=True), follow=True, callback='parse_item'),
        ]
        super(CrawlerSpider, self).__init__(*args, **kwargs)

        '''
        rules = (
            Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
        )
        '''

    def parse_item(self, response):
        # Don't forget to return an object.
        #  self.state['items_count']
        item = {}
        item['local_urls'] = response.url
        external_urls = LinkExtractor(allow=(), deny=self.allowed_domains, unique=True).extract_links(response)
        item['external_urls'] = set()

        for link in external_urls:
            #! THINK TODO check, maybe you need the exact urls not only domains
           # domain = urlparse(link.url).netloc
            item['external_urls'].add(link.url)
      
        #i['domain_id'] = response.xpath('//input[@id="sid"]/@value').extract()
        #i['name'] = response.xpath('//div[@id="name"]').extract()
        #i['description'] = response.xpath('//div[@id="description"]').extract()
        return item

    def parse_impressum(self, response):
        item = {}
        #! THINK TODO XPATH
        self.logger.info(response.xpath("//*[contains(text(), 'e. V.')]"))
        item['name'] = 'Medical Valley EMN e. V.'
        item['source_url'] = response.url
        return item
