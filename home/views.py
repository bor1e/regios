from django.shortcuts import render, redirect
from urllib.parse import urlparse
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from uuid import uuid4
from home.models import DomainScrapyItem
import json
import urllib


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

def domain(request):
	crawler = request.session['crawler_details']
	logger.info(type(crawler))
	return render(request, 'home/status.html', crawler)
	#! TODO evtl innerhalb des crawl machen
	#return JsonResponse(crawler)

def crawl(request):

	if request.method == 'POST':
		logger.info("received POST")
		url = request.POST.get('url')
		logger.info("received URL: %s", url)

		if not is_valid_url(url):
			#! TODO THINK 
			logger.warning("URL: %s not validated", url)
			return HttpResponseRedirect('/')

		domain = urlparse(url).netloc # parse the url and extract the domain
		logger.info("extracted domain: %s", domain)
		unique_id = str(uuid4()) # create a unique ID. 

		# This is the custom settings for scrapy spider.
		settings = {
			'unique_id': unique_id, # unique ID for each record for DB
			'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
		}

		# Here we schedule a new crawling task from scrapyd. 
		# Notice that settings is a special argument name. 
		# But we can pass other arguments, though.
		# This returns a ID which belongs and will be belong to this task
		# We are goint to use that to check task's status.
		task = scrapyd.schedule('default', 'crawler', 
			settings=settings, url=url, domain=domain)
		request.session['crawler_details'] = {'domain': domain, 'task_id': task, 'unique_id': unique_id, 'status': 'started' }
		return redirect('domain')


	elif request.method == 'GET':
		# We were passed these from past request above. Remember ?
		# They were trying to survive in client side.
		# Now they are here again, thankfully. <3
		# We passed them back to here to check the status of crawling
		# And if crawling is completed, we respond back with a crawled data.
		task_id = request.GET.get('task_id', None)
		unique_id = request.GET.get('unique_id', None)

		if not task_id or not unique_id:
			return JsonResponse({'error': 'Missing args'})

		# Here we check status of crawling that just started a few seconds ago.
		# If it is finished, we can query from database and get results
		# If it is not finished we can return active status
		# Possible results are -> pending, running, finished
		status = scrapyd.job_status('default', task_id)
		crawler = request.session['crawler_details']
		crawler['status'] = status
		if status == 'finished':
			try:
				logger.debug('received status finished')
				# this is the unique_id that we created even before crawling started.
				item = DomainScrapyItem.objects.get(unique_id=unique_id)
				name = item.name
				local_urls = item.local_urls[1:-1].replace('\'','').replace(' ','').split(',')
				external_domains = item.external_domains[1:-1].replace('\'','').replace(' ','').split(',')
				stats = {
					'name': name,
					'local_urls': len(local_urls),
					'external_domains': len(external_domains),
					'status': status,
					'domain': crawler['domain'],
				}
				#!return JsonResponse({'data': item.to_dict['data']})
				return render(request, 'home/status.html', stats)
			except Exception as e:
				return JsonResponse({'error': str(e)})
		else:
			return render(request, 'home/status.html', crawler)

	return HttpResponseRedirect('/ERROR/')

