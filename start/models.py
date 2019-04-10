from django.db import models
from filter.models import BlackList
from django.db.models import Q

from utils.helpers import get_domain_from_url, clean_url

from scrapyd_api import ScrapydAPI

from datetime import timedelta
import logging
logger = logging.getLogger(__name__)
# connect scrapyd service
localhost = 'http://localhost:6800'
scrapyd = ScrapydAPI(localhost)


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
        logger.info('{} instance status: {}'.format(self.domain,
                                                    self.status))
        status = self.status
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
        if self.has_external_spider() and \
           self.externalspider.reason == 'shutdown':
            self.status = 'canceled'
        elif self.has_info_spider() and self.infospider.reason == 'shutdown':
            self.status = 'canceled'
        elif self.has_external_spider() and \
                self.externalspider.reason and \
                self.externalspider.reason != 'finished':
            self.status = 'refresh'
        elif self.has_info_spider() and \
                self.infospider.reason and \
                self.infospider.reason != 'finished':
            self.status = 'refresh'

        if status != self.status:
            logger.info('{} instance status changed: {}'.format(self.domain,
                                                                self.status))

        super(Domains, self).save(*args, **kwargs)

    def __str__(self):
        return self.domain

    def _filtered_externals(self):
        externals = Externals.objects.filter(domain=self)
        local_ignored = LocalIgnore.objects.filter(domain=self).\
            values_list('ignore', flat=True)
        on_BlackList = BlackList.objects.all().values_list('ignore', flat=True)
        ignore_external_pks = [external.pk for external in externals
                               if external.external_domain in local_ignored or
                               external.external_domain in on_BlackList]

        return externals.exclude(
            pk__in=ignore_external_pks
        )

    def _total_filtered_externals(self):
        externals = Externals.objects.filter(domain=self).count()
        return externals - self._filtered_externals().count()

    # TODO DeprecationWarning
    def _to_scan(self):
        externals = self._filtered_externals()
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

    def _filter_unique_externals_list(self):
        externals = self._unique_external_domains()
        local_ignored = LocalIgnore.objects.filter(domain=self).\
            values_list('ignore', flat=True)
        on_BlackList = BlackList.objects.all().values_list('ignore', flat=True)
        filtered_unique = [external for external in externals
                           if external not in local_ignored and external
                           not in on_BlackList]
        return filtered_unique

    def _filter_unique_externals(self):
        externals = Externals.objects.filter(domain=self)
        local_ignored = LocalIgnore.objects.filter(domain=self).\
            values_list('ignore', flat=True)
        on_BlackList = BlackList.objects.all().values_list('ignore', flat=True)
        filtered_externals = [e.external_domain for e in externals
                              if e.external_domain not in local_ignored and
                              e.external_domain not in on_BlackList]
        unique_externals = set(filtered_externals)
        selected_pks = list()
        for i in externals:
            if i.external_domain in unique_externals:
                selected_pks.append(i.pk)
                unique_externals.remove(i.external_domain)

        # no worry about spiders, they are being run with a cut of url - '/'
        return externals.filter(pk__in=selected_pks)

    def _to_external_scan(self):
        externals = self._filter_unique_externals()
        externalscanned = Domains.objects.filter(Q(externalscan=True) |
                                                 Q(fullscan=True)) \
            .values_list('domain', flat=True)
        not_scanned = [e.external_domain for e in externals
                       if e.external_domain not in externalscanned]
        return not_scanned

    def _to_info_scan(self):
        externals = self._filter_unique_externals()
        db_domains = Domains.objects.all().values_list('domain', flat=True)
        not_scanned = [e.external_domain for e in externals
                       if e.external_domain not in db_domains]
        external_list = [e.external_domain for e in externals]

        for d in Domains.objects.all():
            if d.domain in external_list and not d.has_related_info():
                not_scanned.append(d.domain)

        if not self.has_related_info():
            not_scanned.append(self.domain)
        return not_scanned

    def _to_info_scan_urls(self):
        externals = Externals.objects.filter(domain=self)
        domains = self._to_info_scan()
        urls = [clean_url(x.url) for x in externals
                if x.external_domain in domains]

        if not self.has_related_info():
            urls.append(clean_url(self.url))

        return urls

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

    def _is_being_crawled(self):
        being_crawled = ['external_started', 'info_started']
        return (self.status in being_crawled)

    def _duration(self):
        if not self.fullscan:
            return 0
        externalspider = ExternalSpider.objects.get(domain=self)
        infospider = InfoSpider.objects.get(domain=self)
        duration = externalspider.duration + infospider.duration
        seconds = duration.total_seconds()
        duration_string = '{0:2}:{1:2}:{2:5.3f}'.format(int(seconds / 3600),
                                                        int(seconds / 60),
                                                        float(seconds % 60))
        return duration_string

    def _clean_url(self):
        return clean_url(self.url)
    # externals which are NOT on BlackList or Locally_Ignored
    filtered_externals = property(_filtered_externals)
    total_filtered_externals = property(_total_filtered_externals)
    to_scan = property(_to_scan)
    unique_external_domains = property(_unique_external_domains)
    filter_unique_externals = property(_filter_unique_externals)
    to_external_scan = property(_to_external_scan)
    to_info_scan = property(_to_info_scan)
    to_info_scan_urls = property(_to_info_scan_urls)
    cleaned_url = property(_clean_url)
    duration = property(_duration)
    is_being_crawled = property(_is_being_crawled)

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
    desc = models.TextField(max_length=250, null=True)
    keywords = models.TextField(max_length=200, null=True)
    imprint = models.URLField(null=True)
    zip = models.SmallIntegerField(null=True)
    name = models.TextField(max_length=200, null=True)
    misc = models.TextField(null=True)

    def _is_suspicious(self):
        if self.tip:
            return False

        result = True
        if self.title:
            result = False
        if self.name:
            result = False
        if self.imprint:
            result = False

        return result

    is_suspicious = property(_is_suspicious)

    def __str__(self):
        return self.domain.domain


class Externals(models.Model):
    url = models.URLField()
    domain = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        related_name='externals'
    )

    def _get_domain(self):
        return get_domain_from_url(self.url)

    def _info(self):
        domain = get_domain_from_url(self.url)
        if Domains.objects.filter(domain=domain).exists():
            return Domains.objects.get(domain=domain).info
        return

    def _fullscan(self):
        domain = get_domain_from_url(self.url)
        if Domains.objects.filter(domain=domain).exists():
            return Domains.objects.get(domain=domain).fullscan
        return False

    def _is_suspicious(self):
        domain = Domains.objects.get(domain=self.domain)
        my_domain = get_domain_from_url(self.url)
        if my_domain in domain.to_info_scan:
            return True

        if self._info() and self._info().is_suspicious:
            return True

        return False

    def _is_being_crawled(self):
        domain = get_domain_from_url(self.url)
        if not Domains.objects.filter(domain=domain).exists():
            return False
        obj = Domains.objects.get(domain=domain)
        return obj.is_being_crawled

    def _status(self):
        domain = get_domain_from_url(self.url)
        if not Domains.objects.filter(domain=domain).exists():
            return 'not created yet'
        obj = Domains.objects.get(domain=domain)
        return obj.status

    external_domain = property(_get_domain)
    info = property(_info)
    fullscan = property(_fullscan)
    is_suspicious = property(_is_suspicious)
    is_being_crawled = property(_is_being_crawled)
    status = property(_status)

    def __str__(self):
        return self.url

    class Meta:
        unique_together = (('url', 'domain'),)
        ordering = ('url',)


class Locals(models.Model):
    url = models.URLField()
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
    start = models.DateTimeField(auto_now_add=True, null=True)
    finish = models.DateTimeField(null=True)
    duration = models.DurationField(default=timedelta(), null=True)

    robots_forbidden = models.SmallIntegerField(default=0, null=True)
    request_count = models.SmallIntegerField(default=0, null=True)
    log_error_count = models.SmallIntegerField(default=0, null=True)

    def __str__(self):
        return'externalspider of ' + self.domain.domain + ' with job_id: ' + \
            '' + self.job_id


class InfoSpider(models.Model):
    domain = models.OneToOneField(
        Domains,
        on_delete=models.CASCADE,
        related_name='infospider'
    )
    job_id = models.CharField(max_length=80, default='default')
    to_scan = models.SmallIntegerField(default=0, null=True)

    reason = models.TextField(null=True, max_length=80)
    start = models.DateTimeField(auto_now_add=True)
    finish = models.DateTimeField(null=True)
    duration = models.DurationField(default=timedelta(), null=True)

    robots_forbidden = models.SmallIntegerField(default=0, null=True)
    request_count = models.SmallIntegerField(default=0, null=True)
    log_error_count = models.SmallIntegerField(default=0, null=True)

    def save(self, *args, **kwargs):
        super(InfoSpider, self).save(*args, **kwargs)

    def __str__(self):
        return'infospider of ' + self.domain.domain
