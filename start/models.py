from django.db import models
import json 
from urllib.parse import urlparse

import logging 
logger = logging.getLogger(__name__)

class Domains(models.Model):
	# I don't want to use the original id in the web. So a unique
	# unique_id = models.CharField(max_length=100, null=True)
	#! THINK TODO domain to make unique 
	# if you go with unique, you will have to 
	# fetch all the src and targets specifically for that unique_id...
	# makes no sense no unique you can see changes (WHICH CHANGES???) etc. 
	# on the other hand you have a problem when quering...
	domain = models.TextField(max_length=200, unique=True)
	url = models.URLField() 
	status = models.CharField(default='started', max_length=10)
	level = models.SmallIntegerField(default=0) # parent, child, grandchild ...
	duration = models.DurationField(null=True);
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.domain

	class Meta:
		get_latest_by = "updated_at"

class Info(models.Model):
	name = models.CharField(max_length=100)
	title = models.CharField(max_length=100, null=True)
	plz = models.SmallIntegerField(null=True)
	impressum_url = models.URLField()
	# kind = models.CharField(null=True) // e.v. GmbH etc.
	# all other information
	other = models.TextField(null=True)
	# related_name e.g. domain.info.count()
	domain = models.OneToOneField(
		Domains, 
		on_delete=models.CASCADE, 
		related_name='info'
	)

	 # This is for basic and custom serialisation to return it to client as a JSON.
	@property
	def to_dict(self):
		logger.info("Domains being dumped")
		data = {
			#'domain': json.loads(self.domain),
			'name': json.loads(self.name),
			'title': json.loads(self.title),
			'plz': json.loads(self.plz),
			'other': json.loads(self.other),
		}
		return data

	def __str__(self):
		return self.name

class Externals(models.Model):
	url = models.URLField()
	# related_name e.g. domain.externals.count()
	domain = models.ForeignKey(
		Domains, 
		on_delete=models.CASCADE, 
		related_name='externals'
	)

	#@property
	def _get_domain(self):
		return urlparse(self.url).netloc
	
	# TODO think
	external_domain = property(_get_domain)
	#external_domain = models.TextField(max_length=200)

	def __str__(self):
		return self.url

	class Meta:
		unique_together = (('url','domain'),)
		ordering = ('url',)

class Locals(models.Model):
	url = models.URLField()
	# related_name e.g. domain.locals.count()
	domain = models.ForeignKey(
		Domains, 
		on_delete=models.CASCADE, 
		related_name='locals'
	) 

	def __str__(self):
		return self.url

	class Meta:
		unique_together = (('url','domain'),)
