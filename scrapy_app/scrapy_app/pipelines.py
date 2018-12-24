from start.models import Domains, Info, Externals, Locals
# import json
# from urllib.parse import urlparse
from django.core.exceptions import ObjectDoesNotExist

import logging
logger = logging.getLogger(__name__)


class ItemPipeline(object):
    def __init__(self, domain, *args, **kwargs):
        self.domain = domain
        self.name = 'dummy'
        self.zip = '0'
        self.title = ''
        self.impressum_url = '-----'
        self.locals_url = set()
        self.external_urls = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            domain=crawler.spider.domain,
        )

    def close_spider(self, spider):
        attr = getattr(spider, 'pipelines', [])
        d = Domains.objects.get(domain=self.domain)
        logger.debug('closing spider for domain: %s ' % d)

        if 'fullscan' in attr:
            objs_l = (Locals(domain=d, url=i) for i in self.locals_url)
            Locals.objects.bulk_create(objs_l)

            objs_e = (Externals(domain=d, url=i) for i in self.external_urls)
            Externals.objects.bulk_create(objs_e)

            Info.objects.create(
                name=self.name,
                impressum_url=self.impressum_url,
                zip=self.zip,
                title=self.title if self.title else 'None!',
                domain=d,
            )

        elif 'info' in attr:
            try:
                obj = Info.objects.get(domain=d)
            except ObjectDoesNotExist:
                obj = None

            if obj:
                logger.debug('updating information of: %s ' % obj)
                obj.name = self.name
                obj.impressum_url = self.impressum_url
                obj.zip = self.zip
                obj.title = self.title.pop() if self.title else 'None!'
                obj.save()
            else:
                i = Info.objects.create(
                    name=self.name,
                    impressum_url=self.impressum_url,
                    zip=self.zip,
                    title=self.title if self.title else 'None!',
                    domain=d,
                )
                logger.debug('info created: %s ' % i)

        elif 'external' in attr:
            objs_l = (Locals(domain=d, url=i) for i in self.locals_url)
            Locals.objects.bulk_create(objs_l)

            objs_e = (Externals(domain=d, url=i) for i in self.external_urls)
            Externals.objects.bulk_create(objs_e)

        else:
            return

    def process_item(self, item, spider):
        logger.debug('spider: %s' % spider.__dict__)

        if 'name' in item and not item['name'] == '':
            self.name = item['name']
        if 'zip' in item:
            self.zip = item['zip']
        if 'alternative_name' in item and not item['alternative_name'] == '':
            if self.name == 'dummy':
                self.name = item['alternative_name']
            else:
                self.name += item['alternative_name']
        if 'impressum_url' in item:
            self.impressum_url = item['impressum_url']
        if 'title' in item:
            self.title = item['title']
        if 'locals_url' in item:
            self.locals_url.add(item['locals_url'])
        if 'external_urls' in item:
            for url in item['external_urls']:
                self.external_urls.add(url)
        # closing the spider manually for specific info scan
        if 'info' in getattr(spider, 'pipelines', []):
            spider.close_spider = True

        logger.debug('clsoing spider: %s' % spider.__dict__)
        return item
