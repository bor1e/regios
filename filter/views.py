from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import BlackList
from start.models import Domains, LocalIgnore
from django.core.exceptions import ObjectDoesNotExist

import logging
logger = logging.getLogger(__name__)


def add_to_blacklist(request, src_domain, external_domain):
    if not BlackList.objects.filter(ignore=external_domain).exists():
        logger.debug("%s added to ignore list." % external_domain)
        BlackList.objects.create(src_domain=src_domain, ignore=external_domain)

    logger.debug("BlackList has %s elements" % BlackList.objects.count())

    return redirect('display', domain=src_domain)


def add_to_localfilter(request, domain, local_ignore):
    if not LocalIgnore.objects.filter(local_ignore=local_ignore).exists():
        try:
            _domain = Domains.objects.get(domain=domain)
        except ObjectDoesNotExist:
            _domain = Domains.objects.filter(domain__icontains=domain).first()
        logger.debug("%s added to ignore list." % local_ignore)
        LocalIgnore.objects.create(local_ignore=local_ignore, domain=_domain)

    logger.debug("LocalIgnore has {} elements".foramat(
        LocalIgnore.objects.filter(domain=_domain).count()))

    return redirect('display', domain=domain)


def display_filter(request, src_domain=None):
    if not src_domain:
        filtered = BlackList.objects.all()
        return render(request, 'filter.html', {'filtered': filtered})

    # if not BlackList.objects.filter(src_domain=src_domain).exists():
    else:
        domain = Domains.objects.filter(domain__icontains=src_domain)\
            .first()
        externals_list = [e.external_domain for e in domain.externals.all()]
        if BlackList.objects.filter(ignore__in=externals_list).exists():
            filtered = BlackList.objects.filter(ignore__in=externals_list)
            return render(request, 'filter.html', {'filtered': filtered})
        else:
            return HttpResponse('no items for domain: %s' % src_domain)

    # filtered = BlackList.objects.filter(src_domain=src_domain)
    # return render(request, 'filter.html', {'filtered': filtered})


def manual_add_to_blacklist(request):
    ignore = request.POST.get('ignore')
    if not BlackList.objects.filter(ignore=ignore).exists():
        logger.debug("%s added to ignore list." % ignore)
        BlackList.objects.create(src_domain='MANUALLY_ADDED',
                                 ignore=ignore)

    logger.debug("BlackList has %s elements" % BlackList.objects.count())

    filtered = BlackList.objects.all()
    return render(request, 'filter.html', {'filtered': filtered})


def remove_filter(request, ignore):
    if BlackList.objects.filter(ignore=ignore).exists():
        logger.debug("%s removed from ignore list." % ignore)
        BlackList.objects.get(ignore=ignore).delete()

    return redirect('/filter/')


def remove_from_localfilter(request, ignore):
    if LocalIgnore.objects.filter(local_ignore=ignore).exists():
        logger.debug("%s removed from ignore list." % ignore)
        LocalIgnore.objects.get(local_ignore=ignore).delete()

    return redirect('/filter/')
