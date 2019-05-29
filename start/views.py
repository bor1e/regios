from django.shortcuts import render, redirect
from start.models import Domains
from network.models import Network
from django.contrib.auth.decorators import login_required
from utils.helpers import clean_dict
from django.contrib import messages

import logging
logger = logging.getLogger(__name__)


def index(request):
    # check out: https://docs.djangoproject.com/en/2.1/ref/contrib/messages/

    url = request.COOKIES.get('url', None)
    ds = Domains.objects.all().filter(fullscan=True)
    nw = Network.objects.all()

    return render(request, 'index.html', {'url': url, 'domains': ds,
                                          'networks': nw})


def edit_info(request, domain, external):
    keys = {}
    keys['misc'] = request.POST.get('misc', None)
    keys['desc'] = request.POST.get('desc', None)
    keys['keywords'] = request.POST.get('keywords', None)
    keys['zip'] = request.POST.get('zip', None)
    keys = clean_dict(keys)
    if not keys:
        messages.error(request, 'no valid keys found!')
        return redirect('display', domain=domain)

    if not Domains.objects.filter(domain=external).exists():
        msg = '{} could not be found! Please add the domain manually' + \
              ' and then try again.'.format(external)
        messages.error(request, msg)
        return redirect('display', domain=domain)

    e_domain = Domains.objects.get(domain=external)
    if e_domain.has_related_info():
        e_domain.info.__dict__.update(**keys)
        e_domain.info.save()
    else:
        e_domain.info.create(**keys)

    return redirect('display', domain=domain)
