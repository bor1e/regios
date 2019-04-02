from start.models import Domains, Info, Externals, Locals
# import json
# from urllib.parse import urlparse
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

import logging
logger = logging.getLogger(__name__)


class ItemPipeline(object):
    def __init__(self, domain, url, stats, *args, **kwargs):
        self.domain = domain
        self.url = url
        self.stats = stats
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
            url=crawler.spider.url,
            stats=crawler.stats,
        )

    def close_spider(self, spider):
        attr = getattr(spider, 'pipelines', [])
        d, x = Domains.objects.get_or_create(domain=self.domain, url=self.url)
        # logger.debug('closing spider for domain: %s created: %s' % (d, x))
        # logger.debug(self.stats.get_stats()['log_count/ERROR'])

        if 'fullscan' in attr:
            logger.debug('\nBOTSPIDER\n')
            try:
                objs_l = (Locals(domain=d, url=i)
                          for i in self.locals_url)
                objs_e = (Externals(domain=d, url=i)
                          for i in self.external_urls)

                Locals.objects.bulk_create(objs_l)
                Externals.objects.bulk_create(objs_e)

                logger.debug('bot: locals %s' % len(self.locals_url))
                logger.debug('bot: externals %s' % len(self.external_urls))
                i = Info.objects.create(
                    name=self.name,
                    impressum_url=self.impressum_url,
                    zip=self.zip,
                    title=self.title if self.title else 'None!',
                    domain=d,
                )
                logger.debug('info created: %s ' % i)

            except IntegrityError:
                pass
            finally:
                d.fullscan = True
                d.save()

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
                d.status = 'info_finished'
                d.infoscan = True
                d.save()
        elif 'external' in attr:

            objs_l = (Locals(domain=d, url=i) for i in self.locals_url)
            Locals.objects.bulk_create(objs_l)

            objs_e = (Externals(domain=d, url=i) for i in self.external_urls)
            Externals.objects.bulk_create(objs_e)

            d.status = 'external_finished'
            d.externalscan = True
            d.save()
            '''
            spider = d.spider(name='external')
            spider.start = stats.collect.start
            spider.finish = stats.collect.finish
            spider.save()
            '''
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
                self.name += '\n[alt: ' + item['alternative_name'] + ' ]'
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

        # logger.debug('closing spider: %s' % spider.__dict__)
        return item
