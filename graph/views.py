from django.shortcuts import render
import json
from django.http import JsonResponse, HttpResponse
from home.models import Domains
from urllib.parse import urlparse

import logging

logger = logging.getLogger(__name__)

def index(request):
	#logger.info(Domains.objects.order_by('domain').distinct().count())
	return render(request, 'graph/graph.html', {})

def api(request):
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
			'id': i.unique_id,
			'size': (i.externals.count()/100.0), # TODO size depends on amount of external links
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
			edge_id = (i.domain+'_'+ex_domain if i.domain < ex_domain else ex_domain+'_'+i.domain)
			if edge_id not in domain_external:
				domain_external.append(edge_id)
				edge = {
					'id': edge_id, #+ '_' + j, # TODO to be unique if we want to have different directions
					'source': i.unique_id,				
					'target': Domains.objects.filter(domain=ex_domain).first().unique_id,
					'size': 1
				}
				edges.append(edge)
			else:
				# i.e. there exists already a connection between those domains
				for d in edges:
					if d['id'] == edge_id:
						d['size'] += 1
						break
			
	data = {'nodes':nodes, 'edges': edges}

	return JsonResponse({'data': data})

def test(request):
	#return render(request, 'graph/test-1.html', {})
	return render(request, 'graph/index.html', {})
