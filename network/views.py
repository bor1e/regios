from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Network, Relation
from start.models import Domains
from utils.helpers import get_domain_from_url

import logging
logger = logging.getLogger(__name__)


# Create your views here.
def add(request):
    logger.debug('received post: {}'.format(request.POST))
    url = request.POST.get('url', request.COOKIES.get('url', None))
    name = request.POST.get('name', None)
    keywords = request.POST.get('keywords', None)

    if not url or not name:
        logger.debug('received post: {}'.format(request.POST))
        messages.error(request, 'Name/URL of network is missing! Retry.')
        return redirect('start')

    # getting or creating the related domain for url
    domain_name = get_domain_from_url(url)
    obj_domain = None
    if Domains.objects.filter(domain__icontains=domain_name).exists():
        obj_domain = Domains.objects.filter(domain__icontains=domain_name) \
            .first()
        msg = 'Domain: {} exists in DB.'.format(obj_domain.domain)
        messages.info(request, msg)

    if not obj_domain:
        obj_domain = Domains.objects.create(domain=domain_name,
                                            url=url)
        msg = 'Domain: {} was created.'.format(obj_domain.domain)
        messages.success(request, msg)

        # TODO think, whether start spider specially here, or wait till
        # display of created domain is visited. For now decided network is
        # primarly for displaying DB results in graph and not for starting
        # specific scans. For this the user is adviced to visit the given
        # actor

    # getting / creating related network
    obj_network = None
    if Network.objects.filter(name=name).exists():
        obj_network = Network.objects.filter(name=name).first()
        msg = 'Network: {} exists in DB.'.format(obj_network)
        messages.info(request, msg)
    else:
        obj_network = Network.objects.create(name=name,
                                             keywords=keywords)
        msg = 'Network: {} successfully created.'.format(obj_network)
        messages.success(request, msg)

    # eig: network.domains.add(create, related)
    # obj_network.domains.add(obj_domain, through_defaults={'related': True})

    # beatles.members.set([john, paul, ringo, george],
    #    through_defaults={'date_joined': date(1960, 8, 1)})
    # https://docs.djangoproject.com/en/dev/topics/db/models/#extra-fields-on-many-to-many-relationships

    # getting / setting relationship between network and url
    rel, created = Relation.objects.get_or_create(domain=obj_domain,
                                                  network=obj_network,
                                                  related=True)
    if created:
        msg = 'Domain {} is now related to Network {}'.format(obj_domain,
                                                              obj_network)
        messages.success(request, msg)

    return render(request, 'network.html', {'network': obj_network})


def network(request, network_name):

    pass
