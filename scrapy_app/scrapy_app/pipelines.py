from home.models import Domains, Info, Externals, Locals
import json
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)


class ScrapyAppPipeline(object):
	def __init__(self, unique_id, *args, **kwargs):
		#! TODO schedule every two seconds a call to a website with current information
		'''
		import requests
r = 	requests.get("http://example.com/foo/bar")
		'''
		self.unique_id = unique_id
		#! TODO domain is not being parsed, get it from the spider
		#self.domain = domain
		self.local_urls = set()
		self.external_urls = set()
		self.name = set()
		self.source_url = set()
		self.counter = 0
		'''
		self.items = {
			'domain': self.domain,
			'local_urls': self.local_urls,
			'external_domains': self.external_domains,
			'name': self.name,
		}
		'''

	@classmethod
	def from_crawler(cls, crawler):
		return cls(
			#domain = json.dumps(crawler.spider.domain),
			unique_id=crawler.settings.get('unique_id'), # this will be passed from django view
		)

	def close_spider(self, spider):
		# And here we are saving our crawled data with django models.
		#logger.error(self.domain)
		domain = Domains.objects.get(unique_id=self.unique_id)
		#objs_e = (Externals(domain=domain, url=i, external_domain=urlparse(i).netloc) for i in self.external_urls)
		objs_e = (Externals(domain=domain, url=i) for i in self.external_urls)		
		Externals.objects.bulk_create(objs_e)
		objs_l = (Locals(domain=domain, url= i) for i in self.local_urls)
		Locals.objects.bulk_create(objs_l)
		if self.counter>1:
			logger.error('MULTIPLE names in IMPRESSUM of %s found ' % str(domain))
		elif self.counter>0:
			info = Info.objects.create(
				name=self.name.pop(), 
				source_url=self.source_url.pop(),
				other=self.counter,
				domain=domain,
			)

	def process_item(self, item, spider):
		if 'local_urls' in item:
			self.local_urls.add(item['local_urls'])
			for url in item['external_urls']:
				self.external_urls.add(url)
		elif 'name' in item:
			self.name.add(item['name'])
			self.source_url.add(item['source_url'])
			self.counter += 1
		return item