from start.models import Domains, ExternalSpider
from utils.helpers import get_domain_from_url
# from filter.models import BlackList
# from django.http import HttpResponse, JsonResponse  # , HttpResponseRedirect,
# from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect  # , reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from scrapyd_api import ScrapydAPI

import time
import logging
logger = logging.getLogger(__name__)


@login_required
def check(request):
    """ Check if the passed paramter named 'url' exists in DB,
    if not, start the spider, otherwise display result
    for the url. """

    url = request.POST.get('url', request.COOKIES.get('url', None))

    if not url:
        logger.debug('check received wrong request method.')
        messages.error(request, 'URL is missing!')
        return redirect('start')

    domain_name = get_domain_from_url(url)

    if Domains.objects.filter(domain__icontains=domain_name).exists():
        obj = Domains.objects.filter(domain__icontains=domain_name).first()
        msg = 'Domain: {} exists in DB.'.format(obj.domain)
        messages.info(request, msg)
        return redirect('display', domain=obj.domain)

    obj = Domains.objects.create(domain=domain_name, url=url)
    msg = 'Domain: {} was created.'.format(obj.domain)
    messages.success(request, msg)

    return redirect('display', domain=obj.domain)


@csrf_exempt
def externals_selected(request, domain=None):
    selected = request.POST.getlist('selected')
    if domain:
        logger.info('received {} selected list of domains from domain {}'
                    .format(selected, domain))
    if selected:
        for domain in selected:
            try:
                obj = Domains.objects.get(domain=domain)
            except ObjectDoesNotExist:
                obj = Domains.objects.create(domain=domain,
                                             url='http://' + domain)
            if not obj.has_external_spider():
                job_id = _start_spider(obj.domain, [])
                externalspider = ExternalSpider \
                    .objects.create(domain=obj, job_id=job_id,
                                    to_scan=len(obj.to_external_scan))
                obj.status = 'external_started'
                obj.save()
                msg = 'Domain: {} progressing ... NEW {}' \
                    .format(obj.domain, externalspider)
                logger.info(msg)

    being_crawled = [d.pk for d in Domains.objects.all() if d.is_being_crawled]
    logger.info('being_crawled {}  list of domains'
                .format(being_crawled))
    objs = Domains.objects.filter(pk__in=being_crawled)
    logger.info('currently crawling {} domains: {}'
                .format(objs.count(), objs.values_list('domain', flat=True)))

    return render(request, 'crawling.html', {'crawling': objs})


def refresh(request, domain):
    if not Domains.objects.filter(domain=domain).exists():
        return redirect('start')

    d = Domains.objects.filter(domain=domain).first()
    d.infoscan = False

    d.externalscan = False
    d.fullscan = False
    if d.has_external_spider():
        d.externalspider.delete()
    if d.has_info_spider():
        d.infospider.delete()
    if d.has_related_info():
        d.info.delete()
    if d.externals.count() > 0:
        d.externals.all().delete()
    if d.locals.count() > 0:
        d.locals.all().delete()
    d.status = 'refreshing'
    d.save()

    return redirect('display', domain=d.domain)


@login_required
def display(request, domain):
    # domain was given over manually
    if not Domains.objects.filter(domain__icontains=domain).exists():
        request.session['domain'] = domain
        msg = 'Domain {} does not exist in DB, nothing to display!' \
              .format(domain)
        messages.error(request, msg)
        return redirect('start')

    try:
        domain = Domains.objects.get(domain=domain)
    except ObjectDoesNotExist:
        replaced_domain = Domains.objects.filter(
            domain__icontains=domain).first()
        logger.debug('Domain: {} replaced by {}'.format(domain,
                                                        replaced_domain))
        return redirect('display', domain=replaced_domain)

    if domain.fullscan:
        logger.debug('displaying {} '.format(domain))
        if domain.status in ['canceled', 'refresh']:
            msg = 'Please refresh {} since crawl could not be completed.' \
                .format(domain.domain)
            messages.warning(request, msg)

        return render(request, 'display-dev.html', {'domain': domain})
    else:
        logger.debug('progressing {} - status: {}'.format(domain,
                                                          domain.status))
        return redirect('progress', domain=domain)


def progress(request, domain):
    if not Domains.objects.filter(domain__icontains=domain).exists():
        request.session['domain'] = domain
        msg = 'Domain {} does not exist in DB, nothing to display!' \
              .format(domain)
        messages.error(request, msg)
        return redirect('start')

    try:
        obj = Domains.objects.get(domain=domain)
        if obj.fullscan:
            return redirect('display', domain=domain)
    except ObjectDoesNotExist:
        replaced_domain = Domains.objects.filter(
            domain__icontains=domain).first()
        logger.debug('Domain: {} replaced by {}'.format(domain,
                                                        replaced_domain))
        return redirect('display', domain=replaced_domain)

    if obj.has_external_spider():
        msg = 'Domain: {} progressing ... EXISTING externalspider {}' \
            .format(obj.domain, obj.externalspider)
        logger.info(msg)
        return render(request, 'display-dev.html', {'domain': obj})

    job_id = _start_spider(obj.domain)
    externalspider = ExternalSpider \
        .objects.create(domain=obj, job_id=job_id,
                        to_scan=len(obj.to_external_scan))
    obj.status = 'external_started'
    obj.save()

    msg = 'Domain: {} progressing ... NEW {}' \
        .format(domain, externalspider)
    logger.info(msg)
    return render(request, 'display-dev.html', {'domain': obj})


def _start_spider(domain, keywords=None):
    localhost = 'http://localhost:6800'
    scrapyd = ScrapydAPI(localhost)
    job_id = scrapyd.schedule('default', 'externalspider',
                              started_by_domain=domain,
                              keywords=keywords)

    return job_id
