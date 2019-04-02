from django.db import models
import json
from urllib.parse import urlparse
from filter.models import BlackList
from django.db.models import Q

from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class Domains(models.Model):
    domain = models.TextField(max_length=200, unique=True)
    url = models.URLField()
    status = models.CharField(default='created', max_length=10)
    # parent, child, grandchild ...
    level = models.SmallIntegerField(default=0)
    fullscan = models.BooleanField(null=True, default=False)
    # TODO maybe get it via Spiders class .. if two spider exists etc.
    infoscan = models.BooleanField(null=True, default=False)
    externalscan = models.BooleanField(null=True, default=False)
    src_domain = models.TextField(max_length=200, null=True)
    duration = models.DurationField(default=timedelta(), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain

    def _filtered(self):
        # logger.debug('external for {}'.format(self.domain))
        externals = Externals.objects.filter(domain=self)
        # logger.debug(externals.values_list('url', flat=True))
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

    # TODO DeprecationWarning
    def _to_scan(self):
        externals = self._filtered()
        # only because domain exists,
        # does not mean it has not to be scnanned, does it?
        existing = [i.pk for i in externals if i.external_domain
                    in
                    Domains.objects.all().values_list('domain', flat=True)]
        return externals.exclude(pk__in=existing)

    def _unique_external_domains(self):
        externals = Externals.objects.filter(domain=self)
        domains = [i.external_domain for i in externals]
        unique_domains = set(domains)
        return list(unique_domains)

    def _filter_unique_externals(self):
        externals = self._unique_external_domains()
        local_ignored = LocalIgnore.objects.filter(domain=self).\
            values_list('ignore', flat=True)
        on_BlackList = BlackList.objects.all().values_list('ignore', flat=True)
        filtered_unique = [external for external in externals
                           if external not in local_ignored or
                           external not in on_BlackList]
        return filtered_unique

    def _to_external_scan(self):
        externals = self._filter_unique_externals()
        not_scanned = [domain for domain in externals
                       if domain not in
                       Domains.objects.filter(Q(externalscan=True) |
                                              Q(fullscan=True))
                       .values_list('domain', flat=True)]
        return not_scanned

    def _to_info_scan(self):
        externals = self._filter_unique_externals()
        not_scanned = [domain for domain in externals
                       if domain not in
                       Domains.objects.filter(Q(infoscan=True) |
                                              Q(fullscan=True))
                       .values_list('domain', flat=True)]
        return not_scanned

    def has_related_info(self):
        has_info = False
        try:
            has_info = (self.info is not None)
        except Info.DoesNotExist:
            pass
        return has_info

    # externals which are NOT on BlackList or Locally_Ignored
    filtered_externals = property(_filtered)
    to_scan = property(_to_scan)
    unique_external_domains = property(_unique_external_domains)
    filter_unique_externals = property(_filter_unique_externals)
    to_external_scan = property(_to_external_scan)
    to_info_scan = property(_to_info_scan)

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
        return self.domain.domain


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


class Spiders(models.Model):
    name = models.TextField(max_length=80)
    job_id = models.CharField(max_length=80)

    # pot = models.BooleanField(default=False)
    # related_name e.g. domain.externals.count()
    # selected = models.BooleanField(null=True, default=False)
    domain = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        related_name='spiders'
    )
    duration = models.DurationField(default=timedelta(), null=True)
    started = models.DateTimeField(null=True)
    finished = models.DateTimeField(null=True)

    def __str__(self):
        return self.name + ' of ' + self.domain.domain

    class Meta:
        unique_together = (('name', 'domain'),)
        ordering = ('domain',)


def _remove_prefix(domain):
    domain_split = domain.split('.')
    # categorize domains matchmaking of words after skiping 'de','org','com'...
    common_prefixes = ['www', 'er', 'en', 'fr', 'de']
    if domain_split[0] in common_prefixes:
        return _remove_prefix('.'.join(domain_split[1:]))
    else:
        return domain
