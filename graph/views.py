from django.shortcuts import render
from django.http import JsonResponse
from filter.models import BlackList
from start.models import Domains, Externals
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

    displaying = [obj.domain for obj in Domains.objects.all()
                  if obj.domain in non_filtered and obj.fullscan]

    logger.debug('external.displaying %s from external.non_filtered %s' %
                 (len(displaying), len(non_filtered)))

    stats = {
        'domain': domain.domain,
        'filtered': filtered,  # .count()
        'non_filtered': non_filtered,  # .count()
        'displaying': displaying,  # .count()
        'rest': domain.externals.count() - len(displaying),  # .count()
    }
    return render(request, 'graph.html', {'stats': stats})


def init_graph(request, domain):
    db_domain = Domains.objects.get(domain=domain)
    filtered = [obj.external_domain for obj in db_domain.externals.all()
                if obj.external_domain in
                BlackList.objects.values_list('ignore', flat=True)]
    non_filtered = [obj.external_domain for obj in db_domain.externals.all()
                    if obj.external_domain not in filtered]
    # need to add the domain for which the graph was called, because it is not
    # included in the non_filtered list, because it is based on the domain...
    non_filtered.append(domain)
    remaining = Domains.objects.all().filter(domain__in=non_filtered,
                                             fullscan=True)
    nodes = list()
    edges = list()
    domains_counter = initialize_domains(remaining)
    ''' TODO:
    - extract www. from domain prefix
    --> do it on DB level (Domains & Externals)
    --> add spider start_urls & allowed_domains
    OR
    --> when calculating IGNORE www while initializing domains_counter
    '''
    logger.debug('initialized domains_counter: %s' % domains_counter)
    edges_counter = list()
    for d in remaining:
        node = {
            'id': d.domain,
            # size depends on externals sites pointing to that one.
            'size': domains_counter[d.domain] * 3 \
            if domains_counter[d.domain]\
            else 1,
            'label': d.domain
        }
        nodes.append(node)
        for e in d.externals.all():
            e_domain = e.external_domain
            if e_domain not in remaining.values_list('domain', flat=True):
                continue
            # can be seperated if we want a bidrictional graph
            # creating a structure in the dicts:
            edge_id = node['id'] + '_' + e_domain if node['id'] < e_domain \
                else e_domain + '_' + node['id']
            if edge_id not in edges_counter:
                edges_counter.append(edge_id)
                edge = {
                    # TODO to be unique if we want to have different directions
                    'id': edge_id,  # + '_' + j
                    'source': node['id'],
                    'target': Domains.objects.get(domain=e_domain).domain,
                    'size': 1
                }
                edges.append(edge)
            else:
                # i.e. there exists already a connection between those domains
                for edge in edges:
                    if edge['id'] == edge_id:
                        edge['size'] += 1
                        break

    data = {'nodes': nodes, 'edges': edges}

    return JsonResponse({'data': data})


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


def initialize_domains(domains):
    domains_list = [d.domain for d in domains]
    domains_size = {}
    for d in domains_list:
        domains_size[d] = 0

    '''
    # in this case the counter of domains linked to is only based on the
    # selected domains for the fullscan
    # the loop below search the entire DB
    for d in domains:
        for e in d.externals.all():
            if e.external_domain in domains_size:
                domains_size[e.external_domain] += 1
    '''

    # in this case the counter of domains checks all the db for given domain
    for e in Externals.objects.all():
        if e.external_domain in domains_size:
            domains_size[e.external_domain] += 1

    return domains_size


def test(request):
    # return render(request, 'graph/test-1.html', {})
    return render(request, 'graph/index.html', {})
