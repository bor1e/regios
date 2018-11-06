from home.models import DomainScrapyItem
import json

class ScrapyAppPipeline(object):
	def __init__(self, unique_id, *args, **kwargs):
		self.unique_id = unique_id
		self.domain = kwargs.get('domain')
		self.local_urls = []
		self.external_domains = []
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
			unique_id=crawler.settings.get('unique_id'), # this will be passed from django view
		)

	def close_spider(self, spider):
		# And here we are saving our crawled data with django models.
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
			self.local_urls.append(item['local_urls'])
			for external_domain in item['external_domains']:
				self.external_domains.append(external_domain)
		elif 'name' in item:
			self.name = item['name']

		return item