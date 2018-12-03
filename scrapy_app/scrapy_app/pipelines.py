from start.models import Domains, Info, Externals, Locals
import json
from urllib.parse import urlparse

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
			domain = crawler.spider.domain,
			#unique_id=crawler.settings.get('unique_id'), # this will be passed from django view
		)

	def close_spider(self, spider):
		#attr = getattr(spider, 'pipelines', [])
		#if 'impressum' in attr and 'title' in attr:
		#if self.impressum_url != '-----' and self.title:
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
			title=self.title.pop(),
			other=self.other,
			domain=d,
		)


	def process_item(self, item, spider):
		#logger.debug('\n\n\nitem:\n%s\n\n\n' % item)
		#if 'impressum' in getattr(spider, 'pipelines', []):
		if 'name' in item:
			self.name = item['name']
		if 'zip' in item:
			self.zip = item['zip']
		if 'impressum_url' in item:
			self.impressum_url = item['impressum_url']
	#elif 'title' in getattr(spider, 'pipelines', []):
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

class ScrapyAppPipeline(object):
	def __init__(self, *args, **kwargs):
		#self.unique_id = unique_id
		#! TODO domain is not being parsed, get it from the spider
		#self.domain = domain
		self.local_urls = set()
		self.external_urls = set()
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
		pass

		# And here we are saving our crawled data with django models.
		#logger.error(self.domain)
		'''domain = Domains.objects.get(unique_id=self.unique_id)
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
			)'''

   
	#@check_spider_pipeline
	def process_item(self, item, spider):
		'''
		if 'local_urls' in item:
			self.local_urls.add(item['local_urls'])
			for url in item['external_urls']:
				self.external_urls.add(url)
		elif 'name' in item:
			self.name.add(item['name'])
			self.source_url.add(item['source_url'])
			self.counter += 1
		return item
		'''
		pass