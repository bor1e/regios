from start.models import Domains
# from filter.models import BlackList
# from django.http import HttpResponse, JsonResponse  # , HttpResponseRedirect,
from urllib.parse import urlparse
# from django.core import serializers
from django.shortcuts import render, redirect  # , reverse

import logging
logger = logging.getLogger(__name__)


def check(request):
    """ Check if the passed paramter named 'url' exists in DB,
    if not, start the spider, otherwise display result
    for the url. """
    logger.debug(request.COOKIES)

    if not (request.method == 'POST' or request.COOKIES['url']):
        logger.debug('check received wrong request method.')
        # TODO set error for session
        return redirect('start')

    url = ''
    if request.POST.get('url'):
        url = request.POST.get('url')
    else:
        url = request.session['url']
    domain = urlparse(url).netloc
    if Domains.objects.filter(domain=domain).exists():
        return redirect('display', domain=domain)

    d = Domains.objects.create(domain=domain, url=url)
    # logger.debug('Domains object: %s created' % d.__dict__)

    return render(request, 'display.html', {'domain': d})


def refresh(request, domain):
    if not Domains.objects.filter(domain=domain).exists():
        response = redirect('start')
        response.set_cookie('domain', domain)
        return response
    d = Domains.objects.filter(domain=domain).first()
    response = redirect('check')
    response.set_cookie('url', d.url)
    d.delete()
    return response


def display(request, domain):
    # domain was given over manually
    if not Domains.objects.filter(domain=domain).exists():
        request.session['domain'] = domain
        return redirect('start')

    domain = Domains.objects.filter(domain=domain).first()
    data = _get_data(domain)

    return render(request, 'display.html', {'domain': data})


def _get_data(domain):
    duration = domain.duration.total_seconds()
    # logger.debug('externals: %s' % len(externals))
    data = {
        'domain': domain.domain,
        'url': domain.url,
        'duration': '{0}m {1:5.3f}s'.format(int(duration / 60),
                                            float(duration % 60)),
        'status': domain.status,
        'name': domain.info.name,
        'title': domain.info.title,
        'zip': domain.info.zip,
        'other': domain.info.other,
        'locals': domain.locals,
        'filtered_externals': domain.filtered_externals,
        'last_update': domain.updated_at
    }
    return data
