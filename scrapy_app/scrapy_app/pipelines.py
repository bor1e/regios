from start.models import Domains, Info, Externals, Locals
# import json
# from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)


class BotPipeline(object):
    def __init__(self, domain, *args, **kwargs):
        self.domain = domain
        self.name = 'dummy'
        self.zip = '00000'
        self.impressum_url = '-----'
        self.title = set()
        self.other = set()
        self.locals_url = set()
        self.external_urls = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            domain=crawler.spider.domain,
        )

    def close_spider(self, spider):
        attr = getattr(spider, 'pipelines', [])
        if 'fullscan' not in attr:
            return
        # if self.impressum_url != '-----' and self.title:
        d = Domains.objects.filter(domain=self.domain).first()
        objs_l = (Locals(domain=d, url=i) for i in self.locals_url)
        Locals.objects.bulk_create(objs_l)
        objs_e = ''
        '''
        if self.p_external_urls:
            objs_e = (Externals(domain=d, url=i) for i in self.p_external_urls)
            self.other.add('partner')
        else:
            objs_e = (Externals(domain=d, url=i) for i in self.external_urls)
        '''
        objs_e = (Externals(domain=d, url=i) for i in self.external_urls)
        Externals.objects.bulk_create(objs_e)

        Info.objects.create(
            name=self.name,
            impressum_url=self.impressum_url,
            zip=self.zip,
            title=self.title.pop() if self.title else 'None!',
            other=self.other,
            domain=d,
        )

    def process_item(self, item, spider):
        # logger.debug('\n\n\nitem:\n%s\n\n\n' % item)
        # if 'impressum' in getattr(spider, 'pipelines', []):
        if 'name' in item:
            self.name = item['name']
        if 'zip' in item:
            self.zip = item['zip']
        if 'impressum_url' in item:
            self.impressum_url = item['impressum_url']
    # elif 'title' in getattr(spider, 'pipelines', []):
        if 'title' in item:
            self.title.add(item['title'])
        if 'other' in item:
            self.other.add(item['other'])
        if 'locals_url' in item:
            self.locals_url.add(item['locals_url'])
        '''
        if 'p_external_urls' in item:
            for url in item['p_external_urls']:
                self.p_external_urls.add(url)
        '''
        if 'external_urls' in item:
            for url in item['external_urls']:
                self.external_urls.add(url)
        return item


class InfoPipeline(object):
    def __init__(self, domain, *args, **kwargs):
        self.domain = domain
        self.name = 'dummy'
        self.zip = '00000'
        self.title = set()
        self.other = set()
        self.impressum_url = '-----'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            domain=crawler.spider.domain,
        )

    def close_spider(self, spider):
        attr = getattr(spider, 'pipelines', [])
        # logger.warning('HELP: %s ' % spider)
        if 'info' not in attr:
            return
        d = Domains.objects.filter(domain=self.domain).first()
        logger.warning('domain: %s ' % d)

        obj = Info.objects.get(domain=d)
        if obj:
            logger.warning('obj: %s ' % obj)
            obj.name = self.name
            obj.impressum_url = self.impressum_url
            obj.zip = self.zip
            obj.title = self.title.pop() if self.title else 'None!'
            obj.other = self.other
            obj.save()
        else:
            i = Info.objects.create(
                name=self.name,
                impressum_url=self.impressum_url,
                zip=self.zip,
                title=self.title.pop() if self.title else 'None!',
                other=self.other,
                domain=d,
            )
            logger.warning('info: %s ' % i)

    def process_item(self, item, spider):
        if 'name' in item:
            self.name = item['name']
        if 'zip' in item:
            self.zip = item['zip']
        if 'impressum_url' in item:
            self.impressum_url = item['impressum_url']
        if 'title' in item:
            self.title.add(item['title'])
        if 'other' in item:
            self.other.add(item['other'])

        return item
