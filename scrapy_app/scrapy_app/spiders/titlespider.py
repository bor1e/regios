# -*- coding: utf-8 -*-
''' 
InfoSpider extracted from Botspider 
Finds the title of index/home directory and ZIP Code, and name from impressum
'''
import scrapy
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
            'title',
        ])

        TitleSpider.rules = [
            Rule(LinkExtractor(unique=True, allow=('/(?i)(home|index|index\.html)')), callback='parse_title'), # title rule
            Rule(LinkExtractor(allow=('/(?i)impressum')), callback='parse_impressum'), # impressum rule
        ]
        super(TitleSpider, self).__init__(*args, **kwargs)

    def parse_title(self, response):
        item = {}
        item['title'] = response.xpath('//title/text()').extract_first()
        item['urls_checked'] = response.url
        #self.logger.debug('TITLE FOUND %s' % item)
        return item

    def parse_impressum(self, response):
        item = {}
        #! THINK TODO XPATH
        keywords = ['e.V.', 'e. V.', 'GmbH', 'mbH', 'GbR', 'Gesellschaft',
            'OHG', 'KG', 'AG', 'gesellschaft']
        item['impressum_url'] = response.url
        # response.xpath("//*[contains(text(), '" + key  + "')]/text()").re(r'(?i)(gmbh|partner|e\.V\.|e\. V\.|gesellschaft|mbh| ag|kg|gbr|ohg)')
        for key in keywords:
            tmp = 100
            # we GUESS that typically names include max 5 
            #! TODO: no guesses!
            sub = 5
            selector = response.xpath("//*[contains(text(), '" + key  + "')]/text()")
            if not selector:
                continue
            for sel in selector:
                strings = sel.extract().split()
                
                if key == 'e. V.':
                    if 'e.' in strings and 'V.' in strings and len(strings)<tmp:
                        # get shortest paragrapgh including the keyword
                        tmp = len(strings)
                        index = strings.index('V.')
                        
                        # dont go backwards, i.e. negativ; 
                        sub = min(sub, len(strings)-1) 
                        item[key] = strings[index-sub:index+1]
                        if len(strings)-1==index:
                            self.logger.info('found e. V. on the END of the line:\n%s' % strings)
                        else: 
                            self.logger.info('found e. V. in the MIDDLE of the line:\n%s' % item[key])

                        continue
                if key in strings and len(strings)<tmp:          
                    # get shortest paragrapgh including the keyword
                    tmp = len(strings)
                    index = strings.index(key)
                    # dont go backwards, i.e. negativ; 
                    sub = min(sub, len(strings)-1) 
                    item[key] = strings[index-sub:index+1]
                    if len(strings)-1==index:
                        self.logger.info('found %s on the END of the line:\n%s' % (key, strings))
                    else: 
                        self.logger.info('found %s in the MIDDLE of the line:\n%s' % (key, item[key]))

        if 'e.V.' in item and 'e. V.' in item:
            ev = ' '.join(item['e.V.'])
            e_v = ' '.join(item['e. V.'])
            if len(ev) > len(e_v):
                item['name'] = e_v
            else:
                item['name'] = ev

        # zip
        find_zip = response.xpath('//p/text()').extract()
        for i in find_zip:
            i = i.strip().split()
            if i and i[0].isdigit() and len(i[0])==5:
                item['zip'] = i[0]
                break

        return item
