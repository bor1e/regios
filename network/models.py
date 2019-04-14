from django.db import models
from start.models import Domains


# Create your models here.
class Network(models.Model):
    # domains = models.ManyToManyField(Domains,
    #                                  through='Relation')
    domains = models.ManyToManyField(Domains)
    name = models.CharField(max_length=100, unique=True)
    keywords = models.TextField(null=True)
    description = models.TextField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


'''
class Relation(models.Model):
    domain = models.ForeignKey(Domains,
                               on_delete=models.CASCADE)
    network = models.ForeignKey(Network,
                                on_delete=models.CASCADE)
    related = models.BooleanField(default=False)

    def __str__(self):
        return self.network + ' ' + self.domain

    class Meta:
        unique_together = (('network', 'domain'),)
        ordering = ('network',)
'''
