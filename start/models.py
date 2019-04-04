from django.db import models
from filter.models import BlackList
from django.db.models import Q

from utils.helpers import get_domain_from_url

from scrapyd_api import ScrapydAPI
# connect scrapyd service
localhost = 'http://localhost:6800'
scrapyd = ScrapydAPI(localhost)

from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class Domains(models.Model):
    domain = models.TextField(max_length=200, unique=True)
    url = models.URLField()
    # parent, child, grandchild ...
    level = models.SmallIntegerField(default=0)
    src_domain = models.TextField(max_length=200, null=True)
    # crawl info
    fullscan = models.BooleanField(null=True, default=False)
    status = models.CharField(default='created', max_length=10)
    infoscan = models.BooleanField(null=True, default=False)
    externalscan = models.BooleanField(null=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.fullscan:
            if self.infoscan and self.externalscan:
                self.fullscan = True
                self.status = 'finished'
            elif self.externalscan and not self.has_info_spider():
                job_id = scrapyd.schedule('default', 'infospider',
                                          started_by_domain=self.domain,
                                          keywords=[])
                InfoSpider.objects.create(domain=self,
                                          job_id=job_id,
                                          to_scan=len(self._to_info_scan()))
                self.status = 'info_started'

        # if self.infoscan:
        #     self.status = 'info_finished'
        # elif self.externalscan:
        #     self.status = 'external_finished'
        super(Domains, self).save(*args, **kwargs)

    def __str__(self):
        return self.domain

    def _fullscan(self):
        return self.infoscan and self.externalscan

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
        # TODO create values list beforehand and not within!
        not_scanned = [domain for domain in externals
                       if domain not in
                       Domains.objects.filter(Q(infoscan=True) |
                                              Q(fullscan=True))
                       .values_list('domain', flat=True)]
        db_domains = Domains.objects.all().values_list('domain', flat=True)
        not_scanned = [domain for domain in externals
                       if domain not in db_domains]
        return not_scanned

    def has_related_info(self):
        has_info = False
        try:
            has_info = (self.info is not None)
        except Info.DoesNotExist:
            pass
        return has_info

    def has_external_spider(self):
        result = False
        try:
            result = (self.externalspider is not None)
        except ExternalSpider.DoesNotExist:
            pass
        return result

    def has_info_spider(self):
        result = False
        try:
            result = (self.infospider is not None)
        except InfoSpider.DoesNotExist:
            pass
        return result

    # externals which are NOT on BlackList or Locally_Ignored
    # fullscan = property(_fullscan)
    filtered_externals = property(_filtered)
    to_scan = property(_to_scan)
    unique_external_domains = property(_unique_external_domains)
    filter_unique_externals = property(_filter_unique_externals)
    to_external_scan = property(_to_external_scan)
    to_info_scan = property(_to_info_scan)

    class Meta:
        get_latest_by = "updated_at"


class Info(models.Model):
    domain = models.OneToOneField(
        Domains,
        on_delete=models.CASCADE,
        related_name='info'
    )

    tip = models.CharField(max_length=100, default='no suggestions', null=True)
    title = models.CharField(max_length=100, null=True)
    desc = models.CharField(max_length=160, null=True)
    keywords = models.TextField(max_length=200, null=True)
    imprint = models.URLField(null=True)
    zip = models.SmallIntegerField(null=True)
    name = models.TextField(max_length=200, null=True)
    misc = models.TextField(null=True)

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
        return get_domain_from_url(self.url)

    def _info(self):
        domain = get_domain_from_url(self.url)
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


class ExternalSpider(models.Model):
    domain = models.OneToOneField(
        Domains,
        on_delete=models.CASCADE,
        related_name='externalspider'
    )
    job_id = models.CharField(max_length=80, default='default')
    to_scan = models.SmallIntegerField(default=0, null=True)

    reason = models.TextField(null=True, max_length=80)
    start = models.DateTimeField(null=True)
    finish = models.DateTimeField(null=True)
    duration = models.DurationField(default=timedelta(), null=True)

    robots_forbidden = models.SmallIntegerField(default=0, null=True)
    request_count = models.SmallIntegerField(default=0, null=True)
    log_error_count = models.SmallIntegerField(default=0, null=True)

    def __str__(self):
        return'externalspider of ' + self.domain.domain


class InfoSpider(models.Model):
    domain = models.OneToOneField(
        Domains,
        on_delete=models.CASCADE,
        related_name='infospider'
    )
    job_id = models.CharField(max_length=80, default='default')
    to_scan = models.SmallIntegerField(default=0, null=True)

    reason = models.TextField(null=True, max_length=80)
    start = models.DateTimeField(null=True)
    finish = models.DateTimeField(null=True)
    duration = models.DurationField(default=timedelta(), null=True)

    robots_forbidden = models.SmallIntegerField(default=0, null=True)
    request_count = models.SmallIntegerField(default=0, null=True)
    log_error_count = models.SmallIntegerField(default=0, null=True)

    def __str__(self):
        return'infospider of ' + self.domain.domain

    # class Meta:
    #     unique_together = (('unique_id', 'domain'),)
