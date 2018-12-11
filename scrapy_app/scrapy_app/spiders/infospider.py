# -*- coding: utf-8 -*-
'''
InfoSpider extracted from Botspider
Finds the title of index/home directory and ZIP Code, and name from impressum
'''
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re


class InfoSpider(CrawlSpider):
    name = 'infospider'

    def __init__(self, *args, **kwargs):
        self.url = kwargs.get('url')
        self.domain = kwargs.get('domain')
        self.keywords = kwargs.get('keywords')
        self.start_urls = [self.url]
        self.allowed_domains = [self.domain]
        # self.handle_httpstatus_list = [301, 302]

        self.pipelines = set([
            'info',
        ])
        self.logger.info('received keywords %s for domain:\n%s'
                         % (self.keywords, self.domain))

        InfoSpider.rules = [
            # Rule(LinkExtractor(unique=True, allow=(
            #   r'/(?i)(home|index|start|index\.html)')),
            #   callback='parse_title'),
            Rule(LinkExtractor(allow=(
                 '/(?i)(impressum|legalnotices|imprint)')),
                 callback='parse_impressum2'),  # impressum rule
        ]
        super(InfoSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        # if response.status in range(301, 307):
        self.logger.debug('response: %s' % response.url)
        impressum = LinkExtractor(unique=True, allow=(
            '/(?i)impressum|legalnotices|imprint')).extract_links(response)
        if impressum:
            self.logger.debug('impressums: %s' % impressum[0].url)
            return scrapy.Request(impressum[0].url,
                                  callback=self.parse_impressum2,
                                  dont_filter=True)

    def parse_title(self, response):
        item = {}
        item['title'] = response.xpath('//title/text()').extract_first()
        item['urls_checked'] = response.url
        self.logger.debug('title found %s' % item)
        self.run = False
        return item

    def parse_impressum(self, response):
        item = {}
        item = self._get_title(response, item)
        item = self._get_name(response, item)
        item = self._get_zip(response, item)
        self.logger.debug('item: %s ' % item)
        item['impressum_url'] = response.url

        return item

    def _get_title(self, response, item):
        title = response.xpath('//title/text()').extract_first()
        re_title = re.compile('impressum', re.IGNORECASE)
        item['title'] = re_title.sub('', title).replace('|', '')
        return item

    def _get_name(self, response, item):
        keywords = ['e.V.', 'e. V.', 'GmbH', 'mbH', 'GbR', 'Gesellschaft',
                    'OHG', 'KG', 'AG', 'gesellschaft', 'KdöR']
        for key in keywords:
            tmp = 100
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
        elif 'GmbH' in item:
            gmbh = ' '.join(item['GmbH'])
            item['name'] = gmbh
        elif 'AG' in item:
            ag = ' '.join(item['AG'])
            item['name'] = ag

        self.logger.debug('item: %s ' % item)

        return item

    def _get_zip(self, response, item):
        find_zip = response.xpath('//p/text()').extract()
        for i, elem in enumerate(find_zip):
            # self.logger.debug('paragraphs: %s' % i)
            elem = elem.strip().split()
            if elem and elem[0].isdigit() and len(elem[0]) == 5:
                if i > 2 and find_zip[i - 3].strip().split():
                    item['alternative_name'] = find_zip[i - 3] + ' ' + \
                        find_zip[i - 2]
                else:
                    item['alternative_name'] = find_zip[i - 2]
                item['zip'] = elem[0]
                self.logger.debug('alternative_name: %s'
                                  % item['alternative_name'])
                break
            elif elem and 'D-' in elem[0] and len(elem[0]) == 7:
                if i > 2 and find_zip[i - 3].strip().split():
                    item['alternative_name'] = find_zip[i - 3] + ' ' + \
                        find_zip[i - 2]
                else:
                    item['alternative_name'] = find_zip[i - 2]
                self.logger.debug('elem: %s' % elem[0])
                item['zip'] = int(''.join(elem[0][2:]))
                self.logger.debug('alternative_name: %s'
                                  % item['alternative_name'])

                break

        return item
