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
        self.pipelines = set([
            'info',
        ])
        self.logger.info('received keywords %s for domain: %s'
                         % (self.keywords, self.domain))

        InfoSpider.rules = [
            # Rule(LinkExtractor(unique=True, allow=(
            #   r'/(?i)(home|index|start|index\.html)')),
            #   callback='parse_title'),
            Rule(LinkExtractor(allow=(
                 '/(?i)(impressum|legalnotices|imprint|' +
                 'legaldisclosure|corporate-info)')),
                 callback='parse_impressum'),  # impressum rule
        ]
        super(InfoSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        # if response.status in range(301, 307):
        self.logger.debug('response: %s' % response.url)
        impressum = LinkExtractor(unique=True, allow=(
            '/(?i)impressum|legalnotices|legaldisclosure|' +
            'imprint|corporate-info')).\
            extract_links(response)
        if impressum:
            self.logger.debug('impressum: %s' % impressum[0].url)
            return scrapy.Request(impressum[0].url,
                                  callback=self.parse_impressum,
                                  dont_filter=True)
        return None

    def parse_title(self, response):
        item = {}
        item['title'] = response.xpath('//title/text()').extract_first()
        item['urls_checked'] = response.url
        self.logger.debug('title found %s' % item)
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
        item['title'] = re_title.sub('', title).replace('|', '').\
            replace('-', ' ')
        return item

    def _get_name(self, response, item):
        keywords = ['e.V.', 'e. V.', 'GmbH', 'mbH', 'GbR', 'Gesellschaft',
                    'OHG', 'KG', 'AG', 'gesellschaft', 'KdöR']
        for key in keywords:
            # selects elements in Document which contain the keyword
            selector = response.xpath(
                "//*[contains(text(), '" + key + "')]/text()")
            if not selector:
                continue

            # assuming the address line in  impressum containing the keyword
            # has less than 100 letters
            # TODO Problem: it filters the shortest name. Maybe combine with
            # zip search, i.e. if zip two/three lines afterwards, most probably
            # the string is the name
            tmp = 100
            # assuming name including keyword is not more than 5 words
            start = 5
            for sel in selector:
                strings = sel.extract().split()

                if key == 'e. V.':
                    if 'e.' in strings \
                       and 'V.' in strings and len(strings) < tmp:
                        # get shortest paragrapgh including the keyword
                        tmp = len(strings)
                        index = strings.index('V.')

                        # avoiding negativ start e.g. strings[-1:3];
                        start = min(start, len(strings) - 1)
                        item[key] = ' '.join(strings[index - start:index + 1])
                        continue

                elif key in strings and len(strings) < tmp:
                    # get shortest paragrapgh including the keyword
                    tmp = len(strings)
                    index = strings.index(key)
                    # dont go backwards, i.e. negativ;
                    start = min(start, len(strings) - 1)
                    item[key] = ' '.join(strings[index - start:index + 1])

        item['name'] = ''
        evs = False
        if 'e.V.' in item and 'e. V.' in item:
            evs = True
            ev = item['e.V.']
            e_v = item['e. V.']
            # TODO Problem: choosing the shorter version
            verein = ev if len(ev) < len(e_v) else e_v
            item['name'] = verein

        for key in keywords:
            if key in item and not evs:
                item['name'] += item[key]

        self.logger.debug('item: %s ' % item)

        return item

    def _get_zip(self, response, item):
        elements = response.xpath('//p/text()').extract()
        item = self._search_for_zip(elements, item)
        if not getattr(item, 'zip', []):
            elements = response.xpath('//span/text()').extract()
            item = self._search_for_zip(elements, item)
        return item

    def _search_for_zip(self, elements, item):
        for i, elem in enumerate(elements):
            elem = elem.strip().split()
            if elem and elem[0].isdigit() and len(elem[0]) == 5 \
               or 'D-' in elem[0] and len(elem[0]) == 7:
                if i > 2 and elements[i - 3].strip().split():
                    item['alternative_name'] = elements[i - 3] + ' ' + \
                        elements[i - 2]
                else:
                    item['alternative_name'] = elements[i - 2]
                item['zip'] = elem[0] if len(elem[0]) == 5 \
                    else int(''.join(elem[0][2:]))
                self.logger.debug('alternative_name: %s'
                                  % item['alternative_name'])

                break
        return item
