from django.shortcuts import render, redirect
from start.models import Domains
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

import logging
logger = logging.getLogger(__name__)


@login_required
def index(request):
    # TODO! check if session has errors
    ds = Domains.objects.all().filter(fullscan=True)

    return render(request, 'index.html', {'domains': ds})


def edit_zip(request, domain, external):
    zipcode = request.POST.get('edit_zip').strip()
    if not zipcode or not zipcode.isdigit():
        # TODO error message
        return redirect('display', domain=domain)

    try:
        db_domain = Domains.objects.get(domain=external)
    except ObjectDoesNotExist:
        logger.debug('not found : %s' % domain)
        db_domain = Domains.objects.filter(domain__icontains=external).first()
    db_domain.info.zip = zipcode
    db_domain.info.save()
    return redirect('display', domain=domain)


def edit_name(request, domain, external):
    logger.debug(request.POST)
    name = request.POST.get('edit_name').strip()
    if not name:
        # TODO error message
        return redirect('display', domain=domain)

    try:
        db_domain = Domains.objects.get(domain=external)
    except ObjectDoesNotExist:
        logger.debug('not found : %s' % external)
        db_domain = Domains.objects.filter(domain__icontains=external).first()
    db_domain.info.name = name
    db_domain.info.save()
    return redirect('display', domain=domain)
