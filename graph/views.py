from django.shortcuts import render
import json
from django.http import JsonResponse, HttpResponse
from start.models import Domains
from filter.models import BlackList
from urllib.parse import urlparse

import logging

logger = logging.getLogger(__name__)


def index(request, domain):
    # logger.info(Domains.objects.order_by('domain').distinct().count())
    domain = Domains.objects.get(domain=domain)
    filtered = [obj.external_domain for obj in domain.externals.all()
                if obj.external_domain in
                BlackList.objects.values_list('ignore', flat=True)]
    logger.debug('external.filtered: %s' % len(filtered))
    non_filtered = [obj.external_domain for obj in domain.externals.all()
                    if obj.external_domain not in filtered]

    logger.debug('external.non_filtered: %s' % len(non_filtered))

    displaying = [obj.domain for obj in Domains.objects.all()
                  if obj.domain in non_filtered and obj.fullscan]

    logger.debug('external.displaying: %s' % len(displaying))

    stats = {
        'domain': domain.domain,
        'filtered': filtered,  # .count()
        'non_filtered': non_filtered,  # .count()
        'displaying': displaying,  # .count()
        'rest': domain.externals.count() - len(displaying),  # .count()
    }
    return render(request, 'graph.html', {'stats': stats})


def api(request, domain=None):
    domains = set()
    objs = Domains.objects.all()
    check = set(x.domain for x in objs)
    nodes = list()
    edges = list()
    domain_external = list()
    for i in objs:
        if i.domain in domains:
            continue
        node = {
            'id': i.domain,
            # TODO size depends on amount of external links
            'size': (i.externals.count() / 100.0),
            'label': i.domain
        }
        nodes.append(node)
        for external in i.externals.values():
            ex_domain = urlparse(external['url']).netloc
            if ex_domain not in check:
                # we are interested only in nodes which were already scraped
                continue
            # to have a set structure in the dicts;
            # can be seperated if we want a bidrictional graph
            edge_id = (i.domain + '_' + ex_domain if i.domain <
                       ex_domain else ex_domain + '_' + i.domain)
            if edge_id not in domain_external:
                domain_external.append(edge_id)
                edge = {
                    # TODO to be unique if we want to have different directions
                    'id': edge_id,  # + '_' + j
                    'source': i.domain,
                    'target': Domains.objects.filter(domain=ex_domain)\
                                             .first().domain,
                    'size': 1
                }
                edges.append(edge)
            else:
                # i.e. there exists already a connection between those domains
                for d in edges:
                    if d['id'] == edge_id:
                        d['size'] += 1
                        break

    data = {'nodes': nodes, 'edges': edges}

    return JsonResponse({'data': data})


def test(request):
    # return render(request, 'graph/test-1.html', {})
    return render(request, 'graph/index.html', {})
