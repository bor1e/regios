from django.shortcuts import render, redirect, reverse
from start.models import Domains#, BlackList
from django.http import HttpResponse#, HttpResponseRedirect, JsonResponse, 
from urllib.parse import urlparse
from django.core import serializers

import logging 
logger = logging.getLogger(__name__)

def check(request):
	""" Check if the passed paramter named 'url' exists in DB,
	if not, start the spider, otherwise display result 
	for the url. """

	if request.POST.get('url'):
		logger.debug(request.POST.get('url'))
		url = request.POST.get('url')
		domain = urlparse(url).netloc
		if Domains.objects.filter(domain=domain).exists():
			return redirect('display', domain=domain)

		d = Domains.objects.create(domain=domain, url=url)
		#logger.debug('Domains object: %s created' % d.__dict__)

		return render(request, 'display.html', {'domain': d})

	logger.debug('check received wrong request method.')

	# TODO set error for session
	return redirect('start')

def display(request, domain):

	""" The domain was already once scraped, and we can display the information
	we have. A JSON for the DataTable is returned. """
	logger.debug(domain)
	d = Domains.objects.filter(domain=domain)
	fields_to_display = ['domain','duration','name',
		'plz', 'title', 'status', 'other']
	data = serializers.serialize("json", d)


	return HttpResponse('Hello: %s' % data)
