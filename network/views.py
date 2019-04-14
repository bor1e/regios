from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Network  # , Relation
from start.models import Domains, ExternalSpider, Externals
from utils.helpers import get_domain_from_url
from scrapyd_api import ScrapydAPI
from django.http import JsonResponse

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
        # messages.info(request, msg)
        logger.info(msg)

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
        # messages.info(request, msg)
        logger.info(msg)
    else:
        obj_network = Network.objects.create(name=name,
                                             keywords=keywords)
        msg = 'Network: {} successfully created.'.format(obj_network)
        messages.success(request, msg)

    # eig: network.domains.add(create, related)
    # obj_network.domains.add(obj_domain, through_defaults={'related': True})
    obj_network.domains.add(obj_domain)

    # beatles.members.set([john, paul, ringo, george],
    #    through_defaults={'date_joined': date(1960, 8, 1)})
    # https://docs.djangoproject.com/en/dev/topics/db/models/#extra-fields-on-many-to-many-relationships

    # getting / setting relationship between network and url
    # rel, created = Relation.objects.get_or_create(domain=obj_domain,
    #                                               network=obj_network,
    #                                               related=True)
    # if created:
    #     msg = 'Domain {} is now related to Network {}'.format(obj_domain,
    #                                                           obj_network)
    #     messages.success(request, msg)

    # TODO redirect network/network_name
    return redirect('network', network_name=obj_network.name)


def add_domain_to_network(request, network_name):
    url = request.POST.get('url', None)
    if not url:
        logger.debug('check received wrong request method.')
        messages.error(request, 'URL is missing!')
        return redirect('start')

    domain_name = get_domain_from_url(url)

    obj = None
    if Domains.objects.filter(domain__icontains=domain_name).exists():
        obj = Domains.objects.filter(domain__icontains=domain_name).first()
    else:
        obj = Domains.objects.create(domain=domain_name, url=url)
        localhost = 'http://localhost:6800'
        scrapyd = ScrapydAPI(localhost)
        job_id = scrapyd.schedule('default', 'externalspider',
                                  started_by_domain=obj.domain,
                                  keywords=[])
        ExternalSpider.objects.create(domain=obj,
                                      job_id=job_id)
        obj.status = 'external_started'
        obj.save()

    nw = None
    if not Network.objects.filter(name=network_name).exists():
        msg = 'Network: {} not found!'.format(network_name)
        messages.warning(request, msg)
        return redirect('start')

    nw = Network.objects.filter(name=network_name).first()

    nw.domains.add(obj)
    return redirect('network', network_name=nw.name)


def change_domain_relation(request, network_name):
    domain = request.POST.get('domain', None)
    value = request.POST.get('value', None)
    if not domain or not value:
        return JsonResponse({'error': 'argumens missing!'})
    if not Domains.objects.filter(domain=domain).exists():
        return JsonResponse({'error': 'domain not found!'})

    d_obj = Domains.objects.get(domain=domain)
    if not Network.objects.filter(name=network_name).exists():
        return JsonResponse({'error': 'network not found!'})

    network = Network.objects.get(name=network_name)
    if value == 'add':
        network.domains.add(d_obj)
    else:
        network.domains.remove(d_obj)
    network.save()

    return JsonResponse({'status': 'success'})


def network(request, network_name):
    if not Network.objects.filter(name=network_name).exists():
        msg = 'Network: {} not found!'.format(network_name)
        messages.warning(request, msg)
        return redirect('start')

    nw = Network.objects.filter(name=network_name).first()
    external_domains = list()
    for d in nw.domains.all():
        for e in d.filter_unique_externals:
            external_domains.append(e.external_domain)
        # TODO
        # loop over 23000 * len(d) => d > 40 == million loop
        # => need to save referenced by domains somewhere
        for e in Externals.objects.all():
            if e.external_domain == d.domain:
                external_domains.append(e.domain.domain)

    unique_domains = list(set(external_domains))
    suggested_domains = Domains.objects.filter(domain__in=unique_domains)

    return render(request, 'network.html', {'network': nw,
                                            'suggested': suggested_domains})


def update_network(request, network_name):
    keywords = request.POST.get('keywords', None)
    description = request.POST.get('description', None)
    if not (keywords or description):
        logger.info('update fields not found for {} network in {}'
                    .format(network_name, request.POST))
        return redirect('network', network_name=network_name)

    if not Network.objects.filter(name=network_name).exists():
        msg = 'Network: {} not found!'.format(network_name)
        messages.warning(request, msg)
        return redirect('start')
    logger.debug('received kw: {} and {} desc'.format(keywords, description))
    nw = Network.objects.filter(name=network_name).first()
    if keywords:
        nw.keywords = keywords
    if description:
        nw.description = description
    nw.save()
    return redirect('network', network_name=network_name)
