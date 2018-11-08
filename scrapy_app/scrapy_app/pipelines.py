from home.models import DomainScrapyItem
import json
import logging
logger = logging.getLogger(__name__)


class ScrapyAppPipeline(object):
	def __init__(self, unique_id, domain, *args, **kwargs):
		#! TODO schedule every two seconds a call to a website with current information
		'''
		import requests
r = 	requests.get("http://example.com/foo/bar")
		'''
		self.unique_id = unique_id
		#! TODO domain is not being parsed, get it from the spider
		self.domain = domain
		self.local_urls = set()
		self.external_domains = set()
		self.name = ''
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
			domain = json.dumps(crawler.spider.domain),
			unique_id=crawler.settings.get('unique_id'), # this will be passed from django view
		)

	def close_spider(self, spider):
		# And here we are saving our crawled data with django models.
		#logger.error(self.domain)
		item = DomainScrapyItem()
		item.unique_id = self.unique_id
		item.domain = self.domain
		item.local_urls = self.local_urls
		item.external_domains = self.external_domains 
		item.name = self.name
		#item.data = json.dumps(self.items)
		item.save()

	def process_item(self, item, spider):
		if 'local_urls' in item:
			self.local_urls.add(item['local_urls'])
			for external_domain in item['external_domains']:
				self.external_domains.add(external_domain)
		elif 'name' in item:
			self.name = item['name']

		return item