from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import BlackList
import logging
logger = logging.getLogger(__name__)


def add_to_blacklist(request, src_domain, external_domain):
    if not BlackList.objects.filter(ignore=external_domain).exists():
        logger.debug("%s added to ignore list." % external_domain)
        BlackList.objects.create(src_domain=src_domain, ignore=external_domain)

    logger.debug("BlackList has %s elements" % BlackList.objects.count())

    return redirect('display', domain=src_domain)


def display_filter(request, domain):
    # TODO!
    if not BlackList.objects.filter(src_domain=domain).exists():
        return HttpResponse('no items for domain: %s' % domain)

    filtered = BlackList.objects.filter(domain=domain)
    return render(request, 'filter.html', {'filtered': filtered})
