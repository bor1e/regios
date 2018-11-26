from django.shortcuts import render, redirect, reverse
from start.models import Domains#, BlackList
from django.http import HttpResponse, JsonResponse#, HttpResponseRedirect
from urllib.parse import urlparse
from django.views.decorators.csrf import csrf_exempt
import json

from scrapyd_api import ScrapydAPI
# connect scrapyd service
scrapyd = ScrapydAPI('http://localhost:6800')

import logging 
logger = logging.getLogger(__name__)


def multiple(request):
	return HttpResponse('multiple')

def get(request):
	return HttpResponse('get')

@csrf_exempt
def post(request):
	spider = request.POST.dict()
	logger.debug('HERE received data params: %s', spider['domain'])
	
	task_id = scrapyd.schedule('default', spider['name'], 
			url=spider['url'], domain=spider['domain'])

	return JsonResponse( {'domain': spider.domain, 
		'task_id': task_id, 
		'status': 'started'
		})
