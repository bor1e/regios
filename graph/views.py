from django.shortcuts import render
import json
from django.http import JsonResponse, HttpResponse
from home.models import Domains

import logging

logger = logging.getLogger(__name__)

def index(request):
	#logger.info(Domains.objects.order_by('domain').distinct().count())
	return render(request, 'graph/graph.html', {})

def api(request):
	domains = set()
	objs = Domains.objects.all()
	nodes = list()
	for i in objs:
		if i.domain in domains:
			continue
		domains.add(i.domain)
		node = {
			'id': i.unique_id,
			'size': (i.externals.count()/100.0),
			'label': i.domain
		}
		nodes.append(node)
	data = {'nodes':nodes}
	return JsonResponse({'data': data})