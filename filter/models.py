from django.db import models

class BlackList(models.Model):
	ignore = models.TextField(max_length=200, unique=True)
	src_domain = models.TextField(max_length=200)

	def __str__(self):
		return self.ignore
