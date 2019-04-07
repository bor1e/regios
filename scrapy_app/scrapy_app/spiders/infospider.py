import scrapy
from scrapy.spiders import CrawlSpider  # , Rule
from scrapy.linkextractors import LinkExtractor
from utils.helpers import get_domain_from_url
from start.models import Domains
from difflib import SequenceMatcher
# from scrapy import signals
from twisted.internet.error import DNSLookupError
from scrapy.spidermiddlewares.httperror import HttpError
# import pandas as pd
import re
# import urllib.request


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class InfoSpider(CrawlSpider):
    name = 'infospider'

    def __init__(self, *args, **kwargs):
        self.started_by_domain = kwargs.get('started_by_domain')
        obj = Domains.objects.get(domain=self.started_by_domain)
        self.allowed_domains = obj.to_info_scan
        # self.allowed_domains = ['cps-hub-nrw.de']
        self.start_urls = obj.to_info_scan_urls
        self.keywords = kwargs.get('keywords')
        self.domains = {}

    def closed(self, reason):
        '''
        self.logger.debug('ToPandas:\n%s', self.to_pandas())
        url = 'http://localhost:8000/scrapy-greets-django'
        try:
            urllib.request.urlopen(url)
        except urllib.error.HTTPError:
            pass
        # self.logger.info('Localhost called!')
        '''
        pass

    def errback_urls(self, failure):
        # log all failures
        # self.logger.error(repr(failure))
        if failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            # self.logger.error('DNSLookupError on %s', request.url)
            url = 'http://www.' + \
                get_domain_from_url(request.url)
            request = scrapy.Request(url,
                                     callback=self.parse_urls,
                                     meta={'dont_retry': True, 'domain': url})
            return request
        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_urls,
                                 errback=self.errback_urls,
                                 dont_filter=True,
                                 meta={'dont_retry': True, 'domain': url})

    def parse_urls(self, response):
        item = {}
        # get title
        item['title'] = response.xpath('//title/text()').get()
        item['meta_title'] = response.xpath(
            "//meta[@name='title']/@content").get()
        item['meta_og_title'] = response.xpath(
            "//meta[@property='og:title']/@content").get()

        # clean title from startseite, home etc.
        for k, v in item.items():
            if not v:
                continue
            item[k] = self._clean_title(v)
        req_url = 'http://' + response.request._meta['download_slot']
        item['domain'] = get_domain_from_url(req_url)
        item['url'] = response.url

        # get description
        item['meta_description'] = response.xpath(
            "//meta[@name='description']/@content").get()
        item['meta_og_description'] = response.xpath(
            "//meta[@property='og:description']/@content").get()

        # get keywords
        item['meta_keywords'] = response.xpath(
            "//meta[@name='keywords']/@content").get()
        item['meta_og_keywords'] = response.xpath(
            "//meta[@property='og:keywords']/@content").get()

        # get imprint for finding potential zip and name of company
        imprint_keywords = ['impressum', 'imprint', 'legalnotices',
                            'privacy', 'privacy', 'policy',
                            'legaldisclosure', 'corporate-info',
                            'terms-of-service', 'contact', 'kontakt',
                            'about']
        imprint_link_extractor = LinkExtractor(allow=(
            '/(?i)(' + '|'.join(imprint_keywords) + ')'),
            unique=True).extract_links(response)
        urls_with_imprint_keyword = [i.url for i in imprint_link_extractor]

        if len(urls_with_imprint_keyword) > 1:
            for key in imprint_keywords:
                for url in urls_with_imprint_keyword:
                    if key in url:
                        item['imprint'] = url
                        request = scrapy.Request(item['imprint'],
                                                 callback=self.parse_impressum,
                                                 errback=self.errback_urls)
                        request.meta['item'] = item
                        return request
        elif len(urls_with_imprint_keyword) == 1:
            item['imprint'] = urls_with_imprint_keyword[0]
            request = scrapy.Request(item['imprint'],
                                     callback=self.parse_impressum,
                                     errback=self.errback_urls)
            request.meta['item'] = item
            return request
        else:
            domain = item['domain']
            item['tip'] = self._recommend_name(item)
            self.domains[domain] = self._clean(item)
            return self.domains[domain]

    def parse_impressum(self, response):
        item = response.meta['item']
        item['name'] = self._get_name(response)
        zipcode, altname = self._get_zip(response)
        item['zip'] = zipcode
        item['alternative_name'] = altname
        item['tip'] = self._recommend_name(item)

        domain = item['domain']
        self.domains[domain] = self._clean(item)
        return self.domains[domain]

    def _clean(self, item):
        i = {}
        for k, v in item.items():
            if not v:
                continue
            i[k] = v
            if v and not isinstance(v, int):
                i[k] = v.strip()
        return i

    def _recommend_name(self, item):
        domain = get_domain_from_url(item['url'])
        words = re.split(r'\W+', domain)
        common_top_level_domain = ['com', 'org', 'de', 'eu', 'net', 'fr', ]
        for w in words:
            if w in common_top_level_domain:
                words.remove(w)
        match = {}

        tags = ['title', 'meta_og_title', 'meta_title', 'name',
                'alternative_name']
        for tag in tags:
            if tag not in item or not item[tag]:
                continue
            compare = item[tag].split(' ')

            for w in words:
                for c in compare:
                    ratio = similar(w, c.lower())
                    if ratio > 0.7:
                        match[tag] = {'ratio': ratio,
                                      'w_domain': w,
                                      'w_tag': c}

        tmp = 0
        recommend = ''
        for key, values in match.items():
            if float(values['ratio']) > tmp:
                tmp = values['ratio']
                recommend = key
            elif values['ratio'] == tmp and tmp != 0.0:
                recommend = key if len(item[key]) < len(item[recommend]) \
                    else recommend

        return recommend

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

        # self.logger.debug('name: %s ' % name)

        return name['name']

    def _get_zip(self, response):
        docelements = ['p', 'span', 'div', 'strong', 'td']
        zipcode = None
        for elem in docelements:
            elements = response.xpath('//' + elem + '/text()').extract()
            zipcode, altname = self._search_for_zip(elements)
            if zipcode:
                altname = altname if altname else None
                return zipcode, altname

        return None, None

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
                # self.logger.debug('alternative_name: %s'
                #                   % altname)

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
                # self.logger.debug('alternative_name: %s'
                #                  % altname)
                break

        altname = altname.strip()
        return zipcode, altname

    def _clean_title(self, title):
        delims = "[\\-\\|\\–]"
        title.strip()
        title_keys = [key.strip() for key in re.split(delims, title) if key]
        ignore_words = ['startseite', 'start', 'home']
        ignore_words_pattern = r'(' + '|'.join(ignore_words) + ')'
        construct_title = list()
        # self.logger.info('title_keys %s', title_keys)
        for key in title_keys:
            cleaned_key = re.sub(ignore_words_pattern, '', key,
                                 flags=re.IGNORECASE)
            if not cleaned_key:
                continue
            construct_title.append(cleaned_key)
        clean_title = ' '.join(construct_title)
        return clean_title

    def to_pandas(self):
        domains = list()
        keywords = ['title', 'meta_og_title', 'meta_title', 'meta_description',
                    'meta_og_description', 'meta_keywords', 'meta_og_keywords',
                    'imprint', 'name', 'zip', 'alternative_name', 'tip']
        mylist = [[] for _ in range(len(keywords))]
        for key, value in self.domains.items():
            domains.append(key)
            for i, k in enumerate(keywords):
                if k in value and value[k]:
                    if not isinstance(value[k], int):
                        mylist[i].append(value[k][:20])
                    else:
                        mylist[i].append(value[k])
                else:
                    mylist[i].append(None)

        d = {}
        d['domains'] = domains
        for i, k in enumerate(keywords):
            d[k] = mylist[i]

        length_of_elems = len(domains)
        for n, i in enumerate(mylist):
            if len(mylist[n]) != length_of_elems:
                self.logger.error('wrong: %s', keywords[n])

        return d
