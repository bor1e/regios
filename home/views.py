from django.shortcuts import render, redirect
from urllib.parse import urlparse
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from uuid import uuid4
from home.models import Domains, BlackList
import json
import urllib
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import time
from datetime import datetime, timedelta
import random
import logging
from scrapyd_api import ScrapydAPI
# connect scrapyd service
scrapyd = ScrapydAPI('http://localhost:6800')
# start logger
logger = logging.getLogger(__name__)

def is_valid_url(url):
	validate = URLValidator()
	try:
		validate(url) # check if url format is valid
	except ValidationError:
		return False

	return True

# Create your views here.
def index(request):
	logger.info("index page loading")
	return render(request, 'home/index.html', {})

def domain(request, domain):
	#crawler = request.session['crawler_details']
	#! TODO think what to do with previous information about domain
	logger.debug("loading domain: %s from DB" % domain)
	# display Information from DB
	# TODO THINK ask for update? if update rewrite completely?
	if not Domains.objects.filter(domain=domain).exists():
		return redirect('index')
	latest_domain = Domains.objects.filter(domain=domain).latest()

	#filtered = [external for external in latest_domain.externals.all() if external.external_domain in BlackList.objects.all().values_list('ignore', flat=True)]
	#logger.debug("Filtered elements has %s elements" % len(filtered))
	externals = [external for external in latest_domain.externals.all() if external.external_domain not in BlackList.objects.all().values_list('ignore', flat=True)]
	logger.debug("Externals list has %s elements" % len(externals))
	to_crawl = set([x.external_domain for x in externals])
	logger.debug("Externals list has %s elements" % len(externals))
	return render(request, 'home/status.html', {'domain': latest_domain, 'externals': externals, 'to_crawl':len(to_crawl)})

# TODO think, maybe solving it internally
def filter(request, src_domain, external_domain):
	if not BlackList.objects.filter(ignore=external_domain).exists():
		logger.debug("%s added to ignore list." % external_domain)
		BlackList.objects.create(src=src_domain, ignore=external_domain)

	logger.debug("BlackList has %s elements" % BlackList.objects.count())

	return redirect('domain', domain=src_domain)

def external_crawling(request, domain):
	latest_domain = Domains.objects.filter(domain=domain).latest()
	externals = [external for external in latest_domain.externals.all() if external.external_domain not in BlackList.objects.all().values_list('ignore', flat=True)]
	domains_to_crawl = dict(zip([x.external_domain for x in externals],[x.url for x in externals]))
	logger.warning("Domains to crawl: %d", len(domains_to_crawl))
	# TODO
	tries = 50
	run = min(len(domains_to_crawl), tries)
	test_domains = {k: domains_to_crawl[k] for k in list(domains_to_crawl)[:run]}
	return render(request, 'home/external_crawling.html', {
		'externals': test_domains, 'to_crawl':len(test_domains), 'level': (latest_domain.level+1)
		})

@csrf_exempt
def crawl(request):
	if request.method == 'POST':
		domain = ''
		url = ''
		level = 0
		function = request.POST.get('function')
		if function == 'start':
			logger.debug('checking domain ...')
			url = request.POST.get('url')
			logger.info("received URL: %s", url)

			if not is_valid_url(url):
				#! TODO error handling 
				logger.warning("URL: %s not validated", url)
				return HttpResponseRedirect('/')

			domain = urlparse(url).netloc # parse the url and extract the domain
			#logger.info("received domain: %s", domain)
			
			if Domains.objects.filter(domain=domain).exists():
				logger.debug("Domain %s exists .... redirecting " % domain)
				# equivalent to: return HttpResponseRedirect(reverse('post_details', args=(post_id, )))
				return JsonResponse({'domain': domain})
		
		elif function == 'refresh':
			logger.debug('refreshing information ...')
			domain = request.POST.get('domain')
			url = Domains.objects.filter(domain=domain).latest().url
			logger.debug('refreshing information %s...', url)

		elif function == 'ajax':
			domain = request.POST.get('domain')
			if Domains.objects.filter(domain=domain).exists():
				crawling = Domains.objects.filter(domain=domain).latest()
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
					'logs': '-',
					'details': reverse('domain', kwargs={'domain':crawling.domain}),
				}
				return JsonResponse({'data': stats, 'exists': True})
				#return JsonResponse({'exists': domain})
			url = request.POST.get('url')
			level = request.POST.get('level')
		
		elif function == 'debug':
			task = scrapyd.schedule('default', 'quotes')
			logger.debug('Spider Quotes started')	
			return JsonResponse({'status': 'started', 'task_id': task, 'unique_id': 'test'})

		unique_id = str(uuid4()) # create a unique ID. 
		obj = Domains.objects.create(domain=domain, unique_id=unique_id, url=url, level=level)
		logger.debug('domain created with domain: %s ; url: %s, level: %s', domain, url, level)

		# about the website, or if he wants to use it again

		settings = {
			'unique_id': obj.unique_id,
			'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0 Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0.'
		}
		# Here we schedule a new crawling task from scrapyd. 
		# task needed for chekcing the status of scrapyd job
		task = scrapyd.schedule('default', 'crawler', 
			settings=settings, url=obj.url, domain=obj.domain)
		logger.debug('HERE task params: %s', task)
		return JsonResponse( {'domain': obj.domain, 'task_id': task, 'unique_id': obj.unique_id, 'status': 'started' })
	

	elif request.method == 'GET':
		# counter for testing ... 
		if request.GET.get('counter'):
			time.sleep(random.randint(0,2))
			counter = int(request.GET.get('counter'))
			counter += 1
			task_id = request.GET.get('task_id')
			status = scrapyd.job_status('default', task_id)
			duration = 'unknown'
			if status == 'finished':
				jobs = scrapyd.list_jobs('default')
				for i in jobs['finished']:
					if i['id'] == task_id:
						start = datetime.strptime(i['start_time'], '%Y-%m-%d %H:%M:%S.%f')
						end = datetime.strptime(i['end_time'], '%Y-%m-%d %H:%M:%S.%f')
						duration = end-start
						duration = str(timedelta(seconds=duration.seconds))
			return JsonResponse({'counter': counter, 'duration':duration, 'status': status})
		# We were passed these from past request above. Remember ?
		# They were trying to survive in client side.
		# Now they are here again, thankfully. <3
		# We passed them back to here to check the status of crawling
		# And if crawling is completed, we respond back with a crawled data.
		task_id = request.GET.get('task_id', None)
		unique_id = request.GET.get('unique_id', None)
		logger.debug('received status check for task %s', task_id)

		if not task_id or not unique_id:
			return JsonResponse({'error': 'Missing args'})

		# Here we check status of crawling that just started a few seconds ago.
		# If it is finished, we can query from database and get results
		# If it is not finished we can return active status
		# Possible results are -> pending, running, finished
		crawling = Domains.objects.get(unique_id=unique_id)
		status = scrapyd.job_status('default', task_id)
		crawling.status = status
		crawling.save()
		if status == 'finished':
			try:
				logger.debug('received status finished')
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
					'details': reverse('domain',  kwargs={'domain':crawling.domain}),
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
	return HttpResponseRedirect('/ERROR/')
