from start.models import Domains, Info, Locals
import json
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)


class InfoAppPipeline(object):
	def __init__(self, *args, **kwargs):
		self.local_urls = set()
		self.name = set()
		self.source_url = set()
		self.counter = 0

	'''
	@classmethod
	def from_crawler(cls, crawler):
		return cls(
			#domain = json.dumps(crawler.spider.domain),
			#unique_id=crawler.settings.get('unique_id'), # this will be passed from django view
		)
	'''
	def close_spider(self, spider):
		
		#domain = Domains.objects.get(#TODO)
		#objs_e = (Externals(domain=domain, url=i, external_domain=urlparse(i).netloc) for i in self.external_urls)
		#objs_e = (Externals(domain=domain, url=i) for i in self.external_urls)		
		#Externals.objects.bulk_create(objs_e)
		#objs_l = (Locals(domain=domain, url= i) for i in self.local_urls)
		#Locals.objects.bulk_create(objs_l)
		#if self.counter>1:
		#	logger.error('MULTIPLE names in IMPRESSUM of %s found ' % str(domain))
		#elif self.counter>0:
		#	info = Info.objects.create(
		#		name=self.name.pop(), 
		#		source_url=self.source_url.pop(),
		#		other=self.counter,
		#		domain=domain,
		#	)

	def process_item(self, item, spider):
		logger.error('ITEM: %s received' % item)
		logger.error('Spider: %s received' % spider)

		'''
		if 'local_urls' in item:
			self.local_urls.add(item['local_urls'])
			for url in item['external_urls']:
				self.external_urls.add(url)
		elif 'name' in item:
			self.name.add(item['name'])
			self.source_url.add(item['source_url'])
			self.counter += 1
		'''
		return item