from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import BlackList
from start.models import Domains, LocalIgnore
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

import logging
logger = logging.getLogger(__name__)


def add_to_blacklist(request, src_domain, external_domain):
    logger.info('adding {} to blacklist from {}'.format(external_domain,
                                                        src_domain))
    external_domain = _remove_www_at_front(external_domain)
    if not BlackList.objects.filter(ignore=external_domain).exists():
        logger.debug("%s added to ignore list." % external_domain)
        BlackList.objects.create(src_domain=src_domain, ignore=external_domain)

    logger.debug("BlackList has %s elements" % BlackList.objects.count())

    return redirect('display', domain=src_domain)


def add_to_localfilter(request, domain, local_ignore):
    # if not LocalIgnore.objects.filter(ignore=local_ignore).exists():
    try:
        _domain = Domains.objects.get(domain=domain)
    except ObjectDoesNotExist:
        _domain = Domains.objects.filter(domain__icontains=domain).first()
    logger.info("{} added to ignore list.".format(local_ignore))
    LocalIgnore.objects.create(ignore=local_ignore, domain=_domain)

    logger.debug("LocalIgnore has {} elements".format(
        LocalIgnore.objects.filter(domain=_domain).count()))

    return redirect('display', domain=domain)


@login_required
def display_filter(request, src_domain=None):
    if not src_domain:
        filtered = _get_data({}, BlackList.objects.all())
        return render(request, 'filter.html', {'filtered': filtered})

    # if not BlackList.objects.filter(src_domain=src_domain).exists():
    else:
        try:
            domain = Domains.objects.get(domain=src_domain)
        except ObjectDoesNotExist:
            domain = Domains.objects.filter(domain__icontains=src_domain)\
                .first()

        externals_list = [e.external_domain for e in domain.externals.all()]
        filtered = _get_data({}, LocalIgnore.objects.filter(domain=domain))

        if BlackList.objects.filter(ignore__in=externals_list).exists():
            filtered = _get_data(filtered, BlackList.objects
                                 .filter(ignore__in=externals_list))
        logger.info('filtered objects: {}'.format(filtered))
        if len(filtered) > 0:
            return render(request, 'filter.html', {'filtered': filtered})
        else:
            return HttpResponse('no items for domain: %s' % src_domain)

    # filtered = BlackList.objects.filter(src_domain=src_domain)
    # return render(request, 'filter.html', {'filtered': filtered})


def manual_add_to_blacklist(request):
    ignore = request.POST.get('ignore')
    ignore = _remove_www_at_front(ignore)
    if not BlackList.objects.filter(ignore=ignore).exists():
        logger.debug("%s added to ignore list." % ignore)
        BlackList.objects.create(src_domain='MANUALLY_ADDED',
                                 ignore=ignore)

    logger.debug("BlackList has %s elements" % BlackList.objects.count())

    filtered = _get_data({}, BlackList.objects.all())
    return render(request, 'filter.html', {'filtered': filtered})


def remove_filter(request, ignore):
    if BlackList.objects.filter(ignore=ignore).exists():
        logger.debug("%s removed from ignore list." % ignore)
        BlackList.objects.get(ignore=ignore).delete()
    elif LocalIgnore.objects.filter(ignore=ignore).exists():
        logger.debug("%s removed from ignore list." % ignore)
        LocalIgnore.objects.get(ignore=ignore).delete()

    return redirect('/filter/')


def _get_data(filtered, obj):
    for i in obj:
        if i.ignore not in filtered:
            filtered[i.ignore] = i.src_domain
    return filtered


def _remove_www_at_front(external_domain):
    arr = external_domain.split('.')
    if arr[0] == 'www':
        return ''.join(arr[1:])
    else:
        return external_domain
