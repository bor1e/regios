from django.shortcuts import render, redirect
from urllib.parse import urlparse
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from uuid import uuid4
from home.models import Domains, Ignore
import json
import urllib
#from django.views.decorators.csrf import csrf_exempt

from scrapyd_api import ScrapydAPI
# connect scrapyd service
scrapyd = ScrapydAPI('http://localhost:6800')

import logging

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
	latest_domain = Domains.objects.filter(domain=domain).latest()
	#filtered = [external for external in latest_domain.externals.all() if external.external_domain in Ignore.objects.all().values_list('ignore', flat=True)]
	#logger.debug("Filtered elements has %s elements" % len(filtered))
	externals = [external for external in latest_domain.externals.all() if external.external_domain not in Ignore.objects.all().values_list('ignore', flat=True)]
	logger.debug("Externals list has %s elements" % len(externals))
	to_crawl = set([x.external_domain for x in externals])
	logger.debug("Externals list has %s elements" % len(externals))
	return render(request, 'home/status.html', {'domain': latest_domain, 'externals': externals, 'to_crawl':len(to_crawl)})

# TODO think, maybe solving it internally
def filter(request, src_domain, external_domain):
	if not Ignore.objects.filter(ignore=external_domain).exists():
		logger.debug("%s added to ignore list." % external_domain)
		Ignore.objects.create(src=src_domain, ignore=external_domain)

	logger.debug("Ignore list has %s elements" % Ignore.objects.count())

	return redirect('domain', domain=src_domain)

def external_crawling(request, domain):
	latest_domain = Domains.objects.filter(domain=domain).latest()
	externals = [external for external in latest_domain.externals.all() if external.external_domain not in Ignore.objects.all().values_list('ignore', flat=True)]
	domains_to_crawl = dict(zip([x.external_domain for x in externals],[x.url for x in externals]))
	return render(request, 'home/external_crawling.html', {
		'externals': domains_to_crawl, 'to_crawl':len(domains_to_crawl)
		})

	'''
	started_domains = set()
	crawling = dict()
	counter = 0
	for external in externals:
		#debug
		counter += 1
		if counter >2:
			break
		# debug end
		if external.external_domain in started_domains:
			continue
		started_domains.add(external.external_domain)
		crawling['domain'] = external.external_domain
		crawling['url'] = external.url
		crawling['generation'] = latest_domain.generation + 1
		json_response = crawl(request, crawling)
		if json_response is None:
			continue
	'''




def crawl(request):
	if request.method == 'POST':
		domain = ''
		url = ''
		generation = 0
		function = request.POST.get('function')
		if function == 'crawl':
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
				return redirect('domain', domain=domain)
		
		elif function == 'update':
			logger.debug('refreshing information ...')
			domain = request.POST.get('domain')
			url = Domains.objects.filter(domain=domain).latest().url
			logger.debug('refreshing information %s...', url)

		elif function == 'ajax':
			domain = request.POST.get('domain')
			if Domains.objects.filter(domain=domain).exists():
				return JsonResponse({'exists': domain})
			url = request.POST.get('url')
			generation = request.POST.get('generation')
		
		unique_id = str(uuid4()) # create a unique ID. 
		logger.debug('domain created with domain: %s ; url: %s', domain, url)
		obj = Domains.objects.create(domain=domain, unique_id=unique_id, url=url, generation=generation)
		
		# about the website, or if he wants to use it again

		settings = {
			'unique_id': obj.unique_id,
			'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
		}
		# Here we schedule a new crawling task from scrapyd. 
		# task needed for chekcing the status of scrapyd job
		task = scrapyd.schedule('default', 'crawler', 
			settings=settings, url=obj.url, domain=obj.domain)
		logger.debug('HERE task params: %s', task)
		return JsonResponse( {'domain': obj.domain, 'task_id': task, 'unique_id': obj.unique_id, 'status': 'started' })
	

	elif request.method == 'GET':
		# We were passed these from past request above. Remember ?
		# They were trying to survive in client side.
		# Now they are here again, thankfully. <3
		# We passed them back to here to check the status of crawling
		# And if crawling is completed, we respond back with a crawled data.
		task_id = request.GET.get('task_id', None)
		unique_id = request.GET.get('unique_id', None)
		logger.debug('received status check for task %s', )

		if not task_id or not unique_id:
			return JsonResponse({'error': 'Missing args'})

		# Here we check status of crawling that just started a few seconds ago.
		# If it is finished, we can query from database and get results
		# If it is not finished we can return active status
		# Possible results are -> pending, running, finished
		crawling = Domains.objects.get(unique_id=unique_id)
		status = scrapyd.job_status('default', task_id)
		logger.debug(scrapyd.list_jobs('default'))
		crawling.status = status
		crawling.save()
		if status == 'finished':
			try:
				logger.debug('received status finished')
				# this is the unique_id that we created even before crawling started.
				#name = item.name
				#local_urls = item.local_urls[1:-1].replace('\'','').replace(' ','').split(',')
				#external_domains = item.external_domains[1:-1].replace('\'','').replace(' ','').split(',')
				stats = {
					'name': crawling.info.name,
					'local_urls': crawling.locals.count(),
					'external_domains': crawling.externals.count(),
					'status': crawling.status,
					'domain': crawling.domain,
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

def _check_domain(request):
	url = request.POST.get('url')
	logger.info("received URL: %s", url)

	if not is_valid_url(url):
		#! TODO error handling 
		logger.warning("URL: %s not validated", url)
		return HttpResponseRedirect('/')

	domain = urlparse(url).netloc # parse the url and extract the domain
	#logger.info("received domain: %s", domain)
			
	if Domains.objects.filter(domain=domain).exists() and request.POST.get('function') == 'crawl':
		logger.debug("Domain %s exists .... redirecting " % domain)
		# equivalent to: return HttpResponseRedirect(reverse('post_details', args=(post_id, )))
		return redirect('domain', domain=domain)
	#! TODO ask the user if he wants to refresh the data
	# about the website, or if he wants to use it again
	unique_id = str(uuid4()) # create a unique ID. 
	Domains.objects.create(domain=domain, unique_id=unique_id, url=url)
	return _start_scrapyd(domain)

def _start_scrapyd(domain):
	# This is the custom settings for scrapy spider.
	domain = Domains.objects.filter(domain=domain).latest()
	settings = {
		'unique_id': domain.unique_id,
		'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
	}
	# Here we schedule a new crawling task from scrapyd. 
	# task needed for chekcing the status of scrapyd job
	task = scrapyd.schedule('default', 'crawler', 
		settings=settings, url=domain.url, domain=domain.domain)
	logger.debug('HERE task params: %s', task)
	return JsonResponse( {'domain': domain.domain, 'task_id': task, 'unique_id': domain.unique_id, 'status': 'started' })
	#request.session['crawler_details'] = {'domain': domain, 'task_id': task, 'unique_id': unique_id, 'status': 'started' }