# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
# from urllib.parse import urlparse
# from scrapy_app import pipelines
'''
if the pages you want to crawl change on a regular basis you could create
a spider that crawls the sitemap, divides the links up into n chunks,
then starts n other spiders to actually crawl the site.
# https://stackoverflow.com/questions/23047080/sharing-visited-urls-between-multiple-spiders-in-scrapy
'''


class BotSpider(CrawlSpider):
    name = 'botspider'

    def __init__(self, *args, **kwargs):
        # We are going to pass these args from our django view.
        # To make everything dynamic, we need to override
        # them inside __init__ method
        self.url = kwargs.get('url')
        self.domain = kwargs.get('domain')
        # self.unique_id = kwargs.get('unique_id')
        self.keywords = kwargs.get('keywords')
        self.start_urls = [self.url]
        self.allowed_domains = [self.domain]
        self.pipelines = set([
            # 'impressum',
            # 'title',
            # 'locals',
            'fullscan',
        ])

        BotSpider.rules = [
            Rule(LinkExtractor(allow=('/(?i)impressum|imprint')),
                 callback='parse_impressum'),
            Rule(LinkExtractor(unique=True, allow=(
                r'/(?i)(home|index|index\.html)')), callback='parse_title'),
            # Rule(LinkExtractor( \
            # unique=True, allow=('/(?i)(partner|mitglieder|' \
            #   'freunde|teilnehmer)')),
            # callback='parse_partner'),
            Rule(LinkExtractor(unique=True), callback='parse_item'),
            # Callback for partner
            # test_ Rule(LinkExtractor(unique=True),
            # follow=True, callback='parse_item'),
        ]
        super(BotSpider, self).__init__(*args, **kwargs)

    def parse_item(self, response):
        item = {}
        item['locals_url'] = response.url

        external_urls = LinkExtractor(allow=(), deny=self.allowed_domains,
                                      unique=True).extract_links(response)
        item['external_urls'] = set()

        for link in external_urls:
            item['external_urls'].add(link.url)

        return item

    def parse_title(self, response):
        item = {}
        item['title'] = response.xpath('//title/text()').extract_first()
        item['other'] = response.url
        return item

    def _get_name(self, response, item):
        keywords = ['e.V.', 'e. V.', 'GmbH', 'mbH', 'GbR', 'Gesellschaft',
                    'OHG', 'KG', 'AG', 'gesellschaft', 'KdöR']
        for key in keywords:
            tmp = 100
            # we GUESS that typically names include max 5
            # ! TODO: no guesses!
            sub = 5
            selector = response.xpath(
                "//*[contains(text(), '" + key + "')]/text()")
            if not selector:
                continue
            for sel in selector:
                strings = sel.extract().split()

                if key == 'e. V.':
                    if 'e.' in strings \
                       and 'V.' in strings and len(strings) < tmp:
                        # get shortest paragrapgh including the keyword
                        tmp = len(strings)
                        index = strings.index('V.')

                        # dont go backwards, i.e. negativ;
                        sub = min(sub, len(strings) - 1)
                        item[key] = strings[index - sub:index + 1]
                        if len(strings) - 1 == index:
                            self.logger.info('found e. V. END of line:\n%s'
                                             % strings)
                        else:
                            self.logger.info('found e. V. in MID of line:\n%s'
                                             % item[key])
                        continue

                if key in strings and len(strings) < tmp:
                    # get shortest paragrapgh including the keyword
                    tmp = len(strings)
                    index = strings.index(key)
                    # dont go backwards, i.e. negativ;
                    sub = min(sub, len(strings) - 1)
                    item[key] = strings[index - sub:index + 1]
                    if len(strings) - 1 == index:
                        self.logger.info('found %s END of line:\n%s'
                                         % (key, strings))
                    else:
                        self.logger.info('found %s in MID of line:\n%s'
                                         % (key, item[key]))

        if 'e.V.' in item and 'e. V.' in item:
            ev = ' '.join(item['e.V.'])
            e_v = ' '.join(item['e. V.'])
            if len(ev) > len(e_v):
                item['name'] = e_v
            else:
                item['name'] = ev

        return item

    def _get_zip(self, response, item):
        find_zip = response.xpath('//p/text()').extract()
        for i in find_zip:
            i = i.strip().split()
            if i and i[0].isdigit() and len(i[0]) == 5:
                self.logger.debug('item: %s' % item)
                self.logger.debug('i: %s' % i)
                item['zip'] = i[0]
                break
        return item

    def parse_impressum(self, response):
        item = {}
        item = self._get_name(response, item)
        item = self._get_zip(response, item)
        item['impressum_url'] = response.url
        # response.xpath("//*[contains(text(), '" + key  + "')]/text()")
        # .re(r'(?i)(gmbh|partner|e\.V\.|e\. V\.|gesellschaft|mbh|
        # ag|kg|gbr|ohg)')

        return item
