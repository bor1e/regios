from start.models import Domains
# from filter.models import BlackList
# from django.http import HttpResponse, JsonResponse  # , HttpResponseRedirect,
from urllib.parse import urlparse
# from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect  # , reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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

    domain_name = _get_domain_without_prefix_from_url(url)

    if Domains.objects.filter(domain__icontains=domain_name).exists():
        obj = Domains.objects.filter(domain__icontains=domain_name).first()
        msg = 'Domain: {} exists in DB.'.format(obj.domain)
        messages.info(request, msg)
        return redirect('display', domain=obj)

    # this this parameters are set in the refresh function below!
    if request.POST.get('level') and request.POST.get('level') != 0:
        level = request.POST.get('level')
        src_domain = request.POST.get('src_domain')
        obj = Domains.objects.create(domain=domain_name, url=url,
                                     level=level, src_domain=src_domain)
        msg = 'Domain: {} was refreshed.'.format(obj.domain)
        messages.info(request, msg)
    else:
        obj = Domains.objects.create(domain=domain_name, url=url)
        msg = 'Domain: {} was created.'.format(obj.domain)
        messages.info(request, msg)

    return render(request, 'display_2.html', {'domain': obj})


def _get_domain_without_prefix_from_url(url):
    complete_domain = urlparse(url).netloc
    domain_split = complete_domain.split('.')
    common_prefixes = ['www', 'en', 'fr', 'de', 'er', ]

    while domain_split[0] in common_prefixes:
        domain_split = domain_split[1:]

    domain = '.'.join(domain_split)
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

    d.delete()
    return response


@login_required
def display(request, domain):
    # domain was given over manually

    if not Domains.objects.filter(domain__icontains=domain).exists():
        request.session['domain'] = domain
        messages.error(request, 'Domain to display does not exist!')
        return redirect('start')

    try:
        domain = Domains.objects.get(domain=domain)
    except ObjectDoesNotExist:
        replaced_domain = Domains.objects.filter(
            domain__icontains=domain).first()
        logger.debug('Domain: {} replaced by {}}'.format(domain,
                                                         replaced_domain))
        return redirect('display', domain=replaced_domain)

    if domain.fullscan:
        return render(request, 'display.html', {'domain': domain})
    else:
        return render(request, 'display_2.html', {'domain': domain})

    '''
    @deprecated 
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
    '''
    # data = _get_data(domain)


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
