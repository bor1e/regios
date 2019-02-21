from start.models import Domains
# from filter.models import BlackList
# from django.http import HttpResponse, JsonResponse  # , HttpResponseRedirect,
from urllib.parse import urlparse
# from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect  # , reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

import time
import logging
logger = logging.getLogger(__name__)


@login_required
def check(request):
    """ Check if the passed paramter named 'url' exists in DB,
    if not, start the spider, otherwise display result
    for the url. """
    logger.debug(request.COOKIES)

    if not (request.method == 'POST' or request.COOKIES['url']):
        logger.debug('check received wrong request method.')
        # TODO set error for session
        return redirect('start')
    # w1.fau.de
    url = request.POST.get('url', request.COOKIES['url'])

    domain_name = _remove_prefix(urlparse(url).netloc)
    # TODO: if the sites exists already in the db but not fullscan error occurs
    if Domains.objects.filter(domain__icontains=domain_name).exists():
        domain = Domains.objects.filter(domain__icontains=domain_name).first()
        return redirect('display', domain=domain)

    if request.POST.get('level') and request.POST.get('level') != 0:
        level = request.POST.get('level')
        src_domain = request.POST.get('src_domain')
        domain = Domains.objects.create(domain=domain_name, url=url,
                                        level=level, src_domain=src_domain)
    else:
        domain = Domains.objects.create(domain=domain_name, url=url)

    return render(request, 'display.html', {'domain': domain})


def _remove_prefix(domain):
    domain_split = domain.split('.')
    # categorize domains matchmaking of words after skiping 'de','org','com'...
    common_prefixes = ['www', 'er', 'en', 'fr', 'de']
    if domain_split[0] in common_prefixes:
        return _remove_prefix('.'.join(domain_split[1:]))
    else:
        return domain


@csrf_exempt
def externals_selected(request, domain):
    # domain = Domains.objects.get(domain=domain)
    selected = request.POST.getlist('selected')
    logger.debug(request.POST)
    logger.info('received {} selected list of domains'.format(selected))
    now = time.time()
    return render(request, 'external_selected.html', {'selected': selected,
                                                      'timer': now})


def refresh(request, domain):
    if not Domains.objects.filter(domain=domain).exists():
        response = redirect('start')
        return response
    d = Domains.objects.filter(domain=domain).first()
    response = redirect('check')
    response.set_cookie('url', d.url)
    response.set_cookie('level', d.level)
    response.set_cookie('src_domain', d.src_domain)

    # logger.debug('dir - response: %s' % dir(response))
    # logger.debug('__dict__ - response: %s' % response.__dict__)

    d.delete()
    return response


@login_required
def display(request, domain):
    # domain was given over manually
    logger.debug('received : %s' % domain)
    if not Domains.objects.filter(domain__icontains=domain).exists():
        request.session['domain'] = domain
        return redirect('start')

    try:
        domain = Domains.objects.get(domain=domain)
    except ObjectDoesNotExist:
        logger.debug('not found : %s' % domain)
        domain = Domains.objects.filter(domain__icontains=domain).first()
        logger.debug('replaced : %s' % domain)

        return redirect('display', domain=domain)

    if domain.has_related_info():
        data = _get_data(domain)
    else:
        # placeholder if page reloaded in the meantime, because.
        # till finished call
        time.sleep(5)
        if domain.has_related_info():
            data = _get_data(domain)
        else:
            data = _get_placeholder_while_dataloading(domain)

    # data = _get_data(domain)
    return render(request, 'display.html', {'domain': data})


def _get_data(domain):
    duration = domain.duration.total_seconds() if domain.duration else 0

    externals_filtered_domains_in_DB = set(e.external_domain
                                           for e in domain.filtered_externals)
    externals_scanned = Domains.objects.\
        filter(domain__in=externals_filtered_domains_in_DB)

    filtered = domain.externals.count() - domain.filtered_externals.count()
    unique_externals = set(e.external_domain for e in domain.externals.all())

    data = {
        'domain': domain.domain,
        'url': domain.url,
        'duration': '{0}m {1:5.3f}s'.format(int(duration / 60),
                                            float(duration % 60)),
        'status': domain.status,
        'name': domain.info.name,
        'title': domain.info.title,
        'zip': '{:05d}'.format(domain.info.zip),
        'filtered': filtered,
        'other': domain.info.other,
        'locals': domain.locals,
        'unique_externals': unique_externals,
        'filtered_externals': externals_scanned,
        'last_update': domain.updated_at
    }
    return data


def _get_placeholder_while_dataloading(domain):
    data = {
        'domain': domain.domain,
        'url': domain.url,
        'duration': 0,
        'status': domain.status,
        'name': '??',
        'title': '??',
        'zip': 0,
        'filtered': None,
        'other': '??',
        'locals': None,
        'unique_externals': '??',
        'filtered_externals': None,
        'last_update': domain.updated_at
    }
    return data
    '''
    explaining the counter of filtered domains based on medical-valley-emn.de:
    d = Domains.object.get(domain='www.medical-valley-emn.de')
    d.externals.count()  # 92
    unique = set(e.external_domain for e in domain.externals.all())  # 59
    ==> only 59 unique external domains,
    i.e. 33 domains are mentioned more often

    multiple = {}
    for e in domain.externals.all():
        multiple[e.external_domain] = multiple.get(e.external_domain, 0) + 1

    logger.debug(len(multiple) == 59)

    doppelte = 0
    for key, val in multiple.items():
        if int(val) > 1:
            logger.debug('[{}]: {}'.format(key, val))
            doppelte += 1

    doppelte ==> 33 !

    filtered_multiple = {}
    for e in domain.filtered_externals.all():
        filtered_multiple[e.external_domain] = filtered_multiple
                                               .get(e.external_domain, 0) + 1
    anzahl, counter = 0, 0
    for k,v in multiple.items():
        if k not in filtered_multiple:
            logger.debug('[{}]: {}'.format(k, v))
            anzahl += 1
            counter += v
    logger.debug('counter: {}, anzahl der doppelten: {}'
                 .format(counter, anzahl))
    anzahl ==> 18 domains were filtered
    counter ==> 31, this 18 domains were 31 times in the d.externals.all

    externals_to_scan ==> unique - anzahl => 59 - 18 = 41 !
    '''
