from django.shortcuts import render
from django.http import HttpResponse#, HttpResponseRedirect, JsonResponse, 
from start.models import Domains#, BlackList
from django.core import serializers

import logging 
logger = logging.getLogger(__name__)

def index(request):
	""" The first site the user sees. It displays the latest Domains, 
	which have been added to the DB in descending order. 
	The User can enter new URL to scrap. """

	# TODO check if session has errors
	
	# get the current domains (ds) being unique
	ds = Domains.objects.all()
	# pass domains to JSON for DataTables to filter
	data = serializers.serialize("json", ds)
	#!TODO 
	if ds.count()>0:
		logger.debug('data received for Display')
	# check if DB empty will happen on frontend
	# display to user
	return render(request, 'index.html', {'data': data})
