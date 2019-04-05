from scrapy import signals
from start.models import Domains, Info, Externals, Locals, ExternalSpider, \
    InfoSpider
from django.core.exceptions import ObjectDoesNotExist

from utils.helpers import get_domain_from_url

import logging
logger = logging.getLogger(__name__)


class ItemPipeline(object):

    def __init__(self, started_by_domain, crawler, stats, *args, **kwargs):
        self.started_by_domain = started_by_domain
        self.stats = stats
        self.spider = crawler.spider.name
        self.locals_url = set()
        self.external_urls = set()
        crawler.signals.connect(self.save_crawl_stats, signals.spider_closed)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            started_by_domain=crawler.spider.started_by_domain,
            stats=crawler.stats,
            crawler=crawler
        )

    def close_spider(self, spider):
        # saving domain related general info
        if self.spider == 'externalspider':
            src = Domains.objects.get(domain=self.started_by_domain)

            objs_l = (Locals(domain=src, url=i) for i in self.locals_url)
            Locals.objects.bulk_create(objs_l)

            objs_e = (Externals(domain=src, url=i) for i in self.external_urls)
            Externals.objects.bulk_create(objs_e)

            src.status = 'external_finished'
            src.externalscan = True
            src.save()
        if self.spider == 'infospider':
            src = Domains.objects.get(domain=self.started_by_domain)
            src.status = 'info_finished'
            src.infoscan = True
            src.save()
        logger.debug('closing: {} with status of domain: '.format(spider.name,
                                                                  src.status))
        pass

    def save_crawl_stats(self, spider, reason):
        stats = self.stats.get_stats()
        data = {}
        data['start'] = stats['start_time']
        data['finish'] = stats['finish_time']
        data['duration'] = data['finish'] - data['start']
        data['reason'] = stats['finish_reason']
        if 'robotstxt/forbidden' in stats:
            data['robots_forbidden'] = stats['robotstxt/forbidden']
        data['request_count'] = stats['downloader/request_count']
        if 'log_count/ERROR' in stats:
            data['log_error_count'] = stats['log_count/ERROR']

        src = Domains.objects.get(domain=self.started_by_domain)
        spider = None
        if self.spider == 'infospider':
            spider = InfoSpider.objects.get(domain=src)
        elif self.spider == 'externalspider':
            spider = ExternalSpider.objects.get(domain=src)

        spider.__dict__.update(**data)
        spider.save()
        logger.info('{} has saved data: {}'.format(self.spider, data))
        pass

    def process_item(self, item, spider):
        # check!
        if spider.name == 'externalspider':
            self._process_external_spider(item)
        elif spider.name == 'infospider':
            self._process_info_spider(item)

        return item

    def _process_external_spider(self, item):
        if 'locals_url' in item:
            self.locals_url.add(item['locals_url'])
        if 'external_urls' in item:
            for url in item['external_urls']:
                self.external_urls.add(url)
        pass

    def _process_info_spider(self, item):
        data = {}
        data['tip'] = item['tip'] if 'tip' in item else None
        data['title'] = self._select_title(item)
        data['desc'] = self._select_description(item)
        data['keywords'] = self._select_keywords(item)
        data['imprint'] = item['imprint'] if 'imprint' in item else None
        data['zip'] = item['zip'] if 'zip' in item else None
        data['name'] = self._select_name(item)
        data['misc'] = item[item['tip']] if 'tip' in item else None

        src = Domains.objects.get(domain=self.started_by_domain)
        url = item['url']
        crawled_domain = item['domain']
        try:
            domain = Domains.objects.get(domain=crawled_domain)
        except ObjectDoesNotExist:
            domain = Domains.objects.create(domain=crawled_domain,
                                            url=url,
                                            src_domain=src.domain,
                                            level=src.level + 1)

        try:
            info = Info.objects.get(domain=domain)
            logger.info('{} info FOUND and NOT updated'.format(domain.domain))
        except ObjectDoesNotExist:
            info = Info.objects.create(domain=domain)
            logger.info('{} INFO CREATED'.format(domain.domain))

        info.__dict__.update(**data)
        info.save()

        # if self.started_by_domain != crawled_domain:
        #     domain.infoscan = True
        #     domain.save()

    def _select_description(self, item):
        if 'meta_description' in item:
            return item['meta_description'][:250]
        elif 'meta_og_description' in item:
            return item['meta_og_description'][:250]
        else:
            return None

    def _select_keywords(self, item):
        if 'meta_keywords' in item:
            return item['meta_keywords']
        elif 'meta_og_keywords' in item:
            return item['meta_og_keywords']
        else:
            return None

    def _select_title(self, item):
        # favor og title because it is more accurate
        if 'meta_og_title' in item:
            return item['meta_og_title']
        elif 'title' in item:
            return item['title']
        elif 'meta_title' in item:
            return item['meta_title']
        else:
            return None

    def _select_name(self, item):
        name = None
        if 'name' in item:
            name = item['name']
        elif 'alternative_name' in item:
            name = item['alternative_name']
        return name

        '''
        spider.start = data['start']
        spider.finish = data['finish']
        spider.duration = data['duration']
        spider.reason = data['reason']
        if 'robots_forbidden' in data:
            spider.robots_forbidden = data['robots_forbidden']
        spider.request_count = data['request_count']
        if 'log_error_count' in data:
            spider.log_error_count = data['log_error_count']
        '''
        '''
        info.tip = data['tip'] if 'tip' in data else None
        info.title = data['title'] if 'title' in data else None
        info.desc = data['desc'] if 'desc' in data else None
        info.keywords = data['keywords'] if 'keywords' in data else None
        info.imprint = data['imprint'] if 'imprint' in data else None
        info.zip = data['zip'] if 'zip' in data else None
        info.misc = data['misc'] if 'misc' in data else None
        '''
