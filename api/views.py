from django.shortcuts import render, redirect, reverse
from start.models import Domains#, BlackList
from django.http import HttpResponse, JsonResponse#, HttpResponseRedirect
from urllib.parse import urlparse
from django.views.decorators.csrf import csrf_exempt
import json
import time
from datetime import datetime, timedelta

from scrapyd_api import ScrapydAPI
# connect scrapyd service
scrapyd = ScrapydAPI('http://localhost:6800')

import logging 
logger = logging.getLogger(__name__)


def multiple(request):
	return HttpResponse('multiple')

@csrf_exempt
def get(request):
	task_id = request.GET.get('task_id', None)
	domain = request.GET.get('domain', None)
	if not task_id or not domain:
			return JsonResponse({'error': 'Missing args'})
	logger.debug('task_id: %s\ndomain: %s' % (task_id, domain))
	crawling = Domains.objects.get(domain=domain)
	status = scrapyd.job_status('default', task_id)
	crawling.status = status
	crawling.save()
	if status == 'finished':
		logger.debug('RECEIVED status finished')
		try:
			jobs = scrapyd.list_jobs('default')
			for i in jobs['finished']:
				if i['id'] == task_id:
					logger.debug('found job %s', i['id'])
					start = datetime.strptime(i['start_time'], '%Y-%m-%d %H:%M:%S.%f')
					end = datetime.strptime(i['end_time'], '%Y-%m-%d %H:%M:%S.%f')
					duration = end-start
					crawling.duration = duration
					crawling.save()
					duration = str(timedelta(seconds=duration.seconds))
			# this is the unique_id that we created even before crawling started.
			#name = item.name
			#local_urls = item.local_urls[1:-1].replace('\'','').replace(' ','').split(',')
			#external_domains = item.external_domains[1:-1].replace('\'','').replace(' ','').split(',')
			log_placeholder = 'http://localhost:6800/logs/default/crawler/{}.log'
			info_name = '---'
			if hasattr(crawling, 'info'):
				info_name = crawling.info.name
			duration = crawling.duration.total_seconds()
			stats = {
				'name': info_name,
				'locals': crawling.locals.count(),
				'externals': crawling.externals.count(),
				'status': crawling.status,
				'domain': crawling.domain,
				'duration': '{0}:{1:5.3f}'.format(int(duration/60), float(duration%60)),
				'logs': log_placeholder.format(task_id),
				#'details': reverse('domain',  kwargs={'domain':crawling.domain}),
			}
			return JsonResponse({'data': stats})
			#return render(request, 'home/status.html', stats)
		except Exception as e:
			#! TODO error handling 
			return JsonResponse({'error': str(e)})
	else:
		logger.info("STATUS : %s", status)
		return JsonResponse({'status': status})
	
	#! TODO error handling 
	return HttpResponse('ERROR')

@csrf_exempt
def post(request):
	spider = request.POST.dict()
	logger.debug('HERE received data params: %s', spider)
	
	if not Domains.objects.filter(domain=domain).exists():
		Domains.objects.create(domain=spider['domain'], url=spider['url'])
	
	task_id = scrapyd.schedule('default', spider['name'], 
			url=spider['url'], domain=spider['domain'], 
			keywords=spider['keywords'])

	return JsonResponse( {'domain': spider['domain'], 
		'task_id': task_id, 
		'status': 'started'
		})
