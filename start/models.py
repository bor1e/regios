from django.db import models
import json
from urllib.parse import urlparse
from filter.models import BlackList
import logging
logger = logging.getLogger(__name__)


class FilteredExternal(models.Manager):
    def get_queryset(self):
        logger.debug(self.__dict__)
        externals = Externals.objects.filter(domain=self)
        to_ignore = BlackList.objects.all().values('ignore')
        ignore_external_pks = [external.pk for external in externals
                               if external.external_domain in to_ignore]
        return super().get_queryset().exclude(
            pk__in=ignore_external_pks
        )


class Domains(models.Model):
    # I don't want to use the original id in the web. So a unique
    # unique_id = models.CharField(max_length=100, null=True)
    # ! THINK TODO domain to make unique
    # if you go with unique, you will have to
    # fetch all the src and targets specifically for that unique_id...
    # makes no sense no unique you can see changes (WHICH CHANGES???) etc.
    # on the other hand you have a problem when quering...
    domain = models.TextField(max_length=200, unique=True)
    url = models.URLField()
    status = models.CharField(default='started', max_length=10)
    # parent, child, grandchild ...
    level = models.SmallIntegerField(default=0)
    duration = models.DurationField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain

    def _filtered(self):
        externals = Externals.objects.filter(domain=self)
        to_ignore = BlackList.objects.all().values_list('ignore', flat=True)
        ignore_external_pks = [external.pk for external in externals
                               if external.external_domain in to_ignore]
        logger.debug('ignore: %s' % to_ignore)
        logger.debug('pks: %s' % ignore_external_pks)
        return externals.exclude(
            pk__in=ignore_external_pks
        )

    filtered_externals = property(_filtered)

    class Meta:
        get_latest_by = "updated_at"


class Info(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, null=True)
    zip = models.SmallIntegerField(null=True)
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

    # !TODO
    @property
    def to_dict(self):
        data = {
            # 'domain': json.loads(self.domain),
            'name': json.loads(self.name),
            'title': json.loads(self.title),
            'zip': json.loads(self.zp),
            'other': json.loads(self.other),
        }
        return data

    def __str__(self):
        return self.name


class Externals(models.Model):
    url = models.URLField()
    # pot = models.BooleanField(default=False)
    # related_name e.g. domain.externals.count()
    domain = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        related_name='externals'
    )

    # @property
    def _get_domain(self):
        return urlparse(self.url).netloc

    def _info(self):
        if Domains.objects.filter(domain=urlparse(self.url).netloc).exists():
            domain = urlparse(self.url).netloc
            return Domains.objects.filter(domain=domain).first().info
        return

    # TODO think
    external_domain = property(_get_domain)
    info = property(_info)
    # external_domain = models.TextField(max_length=200)

    def __str__(self):
        return self.url

    class Meta:
        unique_together = (('url', 'domain'),)
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
        unique_together = (('url', 'domain'),)
