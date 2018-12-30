# -*- coding: utf-8 -*-
# import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re

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
            Rule(LinkExtractor(allow=(
                 '/(?i)(impressum|legalnotices|imprint|' +
                 'about|legaldisclosure|corporate-info|terms-of-service)')),
                 callback='parse_impressum'),
            Rule(LinkExtractor(unique=True, allow=(
                r'/(?i)(home|start|index|index\.html)')),
                callback='parse_title'),
            Rule(LinkExtractor(unique=True), callback='parse_item'),
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

    def parse_impressum(self, response):
        item = {}
        item['title'] = self._get_title(response)
        item['name'] = self._get_name(response)
        zipcode, altname = self._get_zip(response)
        item['zip'] = zipcode
        item['alternative_name'] = altname
        item['impressum_url'] = response.url
        self.logger.debug('item: %s ' % item)

        return item

    def _get_title(self, response):
        docelement = response.xpath('//title/text()').extract_first()
        re_title = re.compile('impressum', re.IGNORECASE)
        title = re_title.sub('', docelement).replace('|', ' ').\
            replace('-', ' ').strip()
        formated_title = re.sub(' +', ' ', title).strip()
        self.logger.debug('title: %s ' % formated_title)
        return formated_title

    def _get_name(self, response):
        keywords = ['e.V.', 'e. V.', 'GmbH', 'mbH', 'GbR', 'Gesellschaft',
                    'OHG', 'KG', 'AG', 'gesellschaft', 'KdöR', 'Inc', 'INC']
        name = {}
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
                        name[key] = ' '.join(strings[index - start:index + 1])
                        continue

                elif key in strings and len(strings) < tmp:
                    # get shortest paragrapgh including the keyword
                    tmp = len(strings)
                    index = strings.index(key)
                    # dont go backwards, i.e. negativ;
                    start = min(start, len(strings) - 1)
                    name[key] = ' '.join(strings[index - start:index + 1])

        name['name'] = ''
        evs = False
        if 'e.V.' in name and 'e. V.' in name:
            evs = True
            ev = name['e.V.']
            e_v = name['e. V.']
            # TODO Problem: choosing the shorter version, see prev
            verein = ev if len(ev) < len(e_v) else e_v
            name['name'] = verein

        for key in keywords:
            if key in name and not evs:
                name['name'] += name[key]

        self.logger.debug('name: %s ' % name)

        return name['name']

    def _get_zip(self, response):
        docelements = ['p', 'span', 'div', 'strong', 'td']
        zipcode = None
        for elem in docelements:
            elements = response.xpath('//' + elem + '/text()').extract()
            zipcode, altname = self._search_for_zip(elements)
            if zipcode:
                return zipcode, altname

    def _search_for_zip(self, elements):
        zipcode = 0
        altname = ''
        for i, docelem in enumerate(elements):
            elem = docelem.strip().split()
            if not elem:
                continue
            # finds the first zipcode displayed on website. Most probably it is
            # the main one.
            if elem[0].isdigit() and len(elem[0]) == 5 \
               or 'D-' in elem[0] and len(elem[0]) == 7:
                if i > 2 and elements[i - 3].strip().split():
                    altname = elements[i - 3] + ' ' + \
                        elements[i - 2]
                else:
                    altname = elements[i - 2]
                zipcode = elem[0] if len(elem[0]) == 5 \
                    else int(''.join(elem[0][2:]))
                self.logger.debug('alternative_name: %s'
                                  % altname)

                break
            # case: D_-_12345 (_: whitespace) => elem = ['D','-','12345']
            elif elem[0] == 'D' and elem[2] and elem[2].isdigit() \
                    and len(elem[2]) == 5:
                if i > 2 and elements[i - 3].strip().split():
                    altname = elements[i - 3] + ' ' + \
                        elements[i - 2]
                else:
                    altname = elements[i - 2]
                zipcode = elem[2]
                self.logger.debug('alternative_name: %s'
                                  % altname)
                break
            else:
                self.logger.debug('elem: %s'
                                  % docelem)

        return zipcode, altname
