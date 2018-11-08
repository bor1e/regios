import json
from django.db import models
from django.utils import timezone
import logging 

logger = logging.getLogger(__name__)

class DomainScrapyItem(models.Model):
	logger.info("DomainScrapyItem being loaded")
	unique_id = models.CharField(max_length=100, null=True)
	#! THINK TODO domain to make unique
	domain = models.TextField()#unique=True # this stands for the input domain, which was cast in views.crawler
	local_urls = models.TextField() # this stands for our crawled urls from the site
	external_domains = models.TextField() # this stands for found external urls
	name = models.CharField(max_length=100, null=True)
	date = models.DateTimeField(default=timezone.now)
    
    # This is for basic and custom serialisation to return it to client as a JSON.
	@property
	def to_dict(self):
		logger.info("DomainScrapyItem being dumped")
		data = {
			'domain': json.loads(self.domain),
            'local_urls': json.loads(self.local_urls),
			'external_domains': json.loads(self.external_domains),
			'name': json.loads(self.name),
			'date': self.date
		}
		print('\n\n ERROR 2\n\n')
		return data

	def __str__(self):
		return self.domain