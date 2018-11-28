from start.models import Domains, Info, Externals, Locals
import json
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)


class BotPipeline(object):
	def __init__(self, domain, *args, **kwargs):
		self.domain = domain
		self.name = 'dummy'
		self.plz = '00000'
		self.impressum_url = '-----'
		self.title = set()
		self.other = set()

	@classmethod
	def from_crawler(cls, crawler):
		return cls(
			domain = crawler.spider.domain,
			#unique_id=crawler.settings.get('unique_id'), # this will be passed from django view
		)

	def close_spider(self, spider):
		attr = getattr(spider, 'pipelines', [])
		if 'impressum' in attr or 'title' in attr:
			d = Domains.objects.filter(domain=self.domain).first()
			Info.objects.create(
				name=self.name, 
				impressum_url=self.impressum_url,
				plz=self.plz,
				title=self.title.pop(),
				other=self.other,
				domain=d,
			)
		else:
			logger.debug('no ITK ----------')


	def process_item(self, item, spider):
		logger.debug('\n\n\nitem:\n%s\n\n\n' % item)
		#if 'impressum' in getattr(spider, 'pipelines', []):
		if 'name' in item:
			self.name = item['name']
		if 'plz' in item:
			self.plz = item['plz']
		if 'impressum_url' in item:
			self.impressum_url = item['impressum_url']
	#elif 'title' in getattr(spider, 'pipelines', []):
		if 'title' in item:
			self.title.add(item['title'])
		if 'other' in item:
			self.other.add(item['other'])
		#else:
		#	logger.debug('oooooooooooo')
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
		if 'second' in getattr(spider, 'pipelines', []):
			logger.debug('snd is present ------------ ')
			pass
		else: 
			logger.debug(' no SECCCCCCOND')

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
		pass
   
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