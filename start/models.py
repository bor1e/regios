from django.db import models
import json
from urllib.parse import urlparse
from filter.models import BlackList
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


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
    fullscan = models.BooleanField(null=True, default=False)
    src_domain = models.TextField(max_length=200, null=True)
    duration = models.DurationField(default=timedelta(), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain

    def _filtered(self):
        logger.debug('external for {}'.format(self.domain))
        externals = Externals.objects.filter(domain=self)
        logger.debug(externals.values_list('url', flat=True))
        local_ignored = LocalIgnore.objects.filter(domain=self).\
            values_list('ignore', flat=True)
        on_BlackList = BlackList.objects.all().values_list('ignore', flat=True)
        ignore_external_pks = [external.pk for external in externals
                               if external.external_domain in local_ignored or
                               external.external_domain in on_BlackList]
        # logger.debug('ignore_external_pks: {}'
        #            .format(len(ignore_external_pks)))

        return externals.exclude(
            pk__in=ignore_external_pks
        )

    def _to_scan(self):
        externals = self._filtered()
        existing = [i.pk for i in externals if i.external_domain
                    in
                    Domains.objects.all().values_list('domain', flat=True)]
        return externals.exclude(pk__in=existing)

    # externals which are NOT on BlackList or Locally_Ignored
    filtered_externals = property(_filtered)
    to_scan = property(_to_scan)

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
    # selected = models.BooleanField(null=True, default=False)
    domain = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        related_name='externals'
    )

    # @property
    def _get_domain(self):
        return _remove_prefix(urlparse(self.url).netloc)

    def _info(self):
        domain = urlparse(self.url).netloc
        if Domains.objects.filter(domain=domain).exists():
            return Domains.objects.get(domain=domain).info
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


class LocalIgnore(models.Model):
    ignore = models.TextField(max_length=200, unique=True)
    domain = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        related_name='local_ignore'
    )

    def __str__(self):
        return self.ignore

    class Meta:
        unique_together = (('ignore', 'domain'),)

    def _get_domain(self):
        return self.domain.domain

    src_domain = property(_get_domain)


def _remove_prefix(domain):
    domain_split = domain.split('.')
    # categorize domains matchmaking of words after skiping 'de','org','com'...
    common_prefixes = ['www', 'er', 'en', 'fr', 'de']
    if domain_split[0] in common_prefixes:
        return _remove_prefix('.'.join(domain_split[1:]))
    else:
        return domain
