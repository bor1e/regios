from django.shortcuts import render, redirect
from django.http import JsonResponse
from filter.models import BlackList
from start.models import Domains, Externals
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


def index(request, domain=None):
    if not domain:
        externals = [e.url for e in Externals.objects.all()
                     if e.external_domain in BlackList.objects
                     .values_list('ignore',
                                  flat=True)]
        stats = {
            'domain': 'all entries in DB',
            'filtered': BlackList.objects.count(),  # .count()
            'displaying': Domains.objects.all()
                                 .exclude(domain__in=BlackList.objects
                                          .values_list('ignore',
                                                       flat=True)),
            'rest': len(externals),  # .count()
        }
        return render(request, 'graph.html', {'stats': stats})
    try:
        domain = Domains.objects.get(domain=domain)
    except ObjectDoesNotExist:
        domain = Domains.objects.filter(domain__icontains=domain).first()

    if not domain:
        return redirect('/')

    non_filtered_ext = set(obj.external_domain
                           for obj in domain.filtered_externals)
    logger.debug(non_filtered_ext)
    displaying = [obj.domain for obj in Domains.objects.all()
                  if obj.domain in non_filtered_ext and obj.fullscan]

    logger.debug(displaying)

    logger.debug('external.displaying %s from external.non_filtered %s' %
                 (len(displaying), len(non_filtered_ext)))

    stats = {
        'domain': domain.domain,
        'displaying': displaying,  # .count()
        'rest': domain.externals.count() - len(displaying),  # .count()
    }
    return render(request, 'graph.html', {'stats': stats})


def init_graph(request, domain=None):
    remaining = None
    parallel_edges = False
    if domain:
        logger.debug('recieved domain: %s' % domain)

        try:
            db_domain = Domains.objects.get(domain=domain)
        except ObjectDoesNotExist:
            db_domain = Domains.objects.filter(domain__icontains=domain)\
                .first()
        logger.debug('found domain in DB: %s' % db_domain.domain)
        non_filtered_ext = set(obj.external_domain
                               for obj in db_domain.filtered_externals)
        # need to add the domain for which the graph was called
        non_filtered_ext.add(db_domain.domain)
        logger.debug(non_filtered_ext)
        # TODO Problem: medical-valley-emn.de in infoteam.externals and in
        # non_filtered_ext BUT NOT IN DOMAINS OBJECTS ALL!!!
        # ie.: www.medical-valley-emn.de NOT IN medical-valley-emn.de
        remaining = Domains.objects.all().filter(domain__in=non_filtered_ext,
                                                 fullscan=True)
    else:
        remaining = Domains.objects.all().exclude(domain__in=BlackList.objects
                                                  .values_list('ignore',
                                                               flat=True))
    nodes = list()
    edges = list()
    domains_counter = initialize_domains(remaining)

    logger.debug('initialized domains_counter: %s' % domains_counter)
    edges_counter = list()
    # check = set(key for key, item in domains_counter.items())
    check = set()
    for d in remaining:
        # d_domain_cleaned = _remove_prefix(d.domain)
        if d.domain not in check:
            check.add(d.domain)
            node = {
                'id': d.domain,
                # size depends on externals sites pointing to that one.
                # 'size': domains_counter[d_domain_cleaned] * 10 \
                'size': domains_counter[d.domain] \
                if domains_counter[d.domain]\
                else 5,
                'label': d.domain
            }
            nodes.append(node)
        for e in d.externals.all():
            if e.external_domain not in remaining.values_list('domain',
                                                              flat=True):
                continue
            # can be seperated if we want a bidrictional graph
            # creating a structure in the dicts:
            if node['id'] < e.external_domain or parallel_edges:
                edge_id = node['id'] + '_' + e.external_domain
            else:
                edge_id = e.external_domain + '_' + node['id']
            # TODO for parallel_edges inside graph
            edge_id = node['id'] + '_' + e.external_domain

            if edge_id not in edges_counter:
                edges_counter.append(edge_id)
                target_domain = Domains.objects.get(domain=e.external_domain)\
                                               .domain
                edge = {
                    # TODO to be unique if we want to have different directions
                    'id': edge_id,  # + '_' + j
                    'source': node['id'],
                    'target': target_domain,
                    'size': 1,
                    'count': 1,
                }
                edges.append(edge)
                for node in nodes:
                    if node['id'] == target_domain:
                        node['size'] += 2
            else:
                # i.e. there exists already a connection between those domains
                for edge in edges:
                    if edge['id'] == edge_id:
                        # TODO: THINK!
                        edge['size'] += 1
                        edge['count'] += 1
                        break

    data = {'nodes': nodes, 'edges': edges}
    # logger.debug('data: %s' % data)
    return JsonResponse({'data': data})


''' DEPRECATED see init_graph for corrections
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
'''


def initialize_domains(domains):
    domains_list = [d.domain for d in domains]
    domains_size = {}
    for d in domains_list:
        domains_size[d] = 0

    # in this case the counter of domains checks all the db for given domain
    for e in Externals.objects.all():
        if e.external_domain in domains_size:
            domains_size[e.external_domain] += 1

    '''
    # in this case the counter of domains linked to is only based on the
    # selected domains for the fullscan
    # the loop above search the entire DB
    for d in domains:
        for e in d.externals.all():
            if e.external_domain in domains_size:
                domains_size[e.external_domain] += 1
    '''

    return domains_size


def _remove_prefix(domain):
    domain_split = domain.split('.')
    # categorize domains matchmaking of words after skiping 'de','org','com'...
    common_prefixes = ['www', 'er', 'en', 'fr', 'de']
    if domain_split[0] in common_prefixes:
        return _remove_prefix('.'.join(domain_split[1:]))
    else:
        return domain


def test(request):
    # return render(request, 'graph/test-1.html', {})
    # return render(request, 'sigmajs-graphfunctionalities-test.html', {})
    return render(request, 'sigmajs-test2.html', {})
