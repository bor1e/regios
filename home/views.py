from django.shortcuts import render
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)
# Create your views here.
def index(request):
	logger.info("index page loading")
	return render(request, 'home/index.html', {})

def post(request):
	print('syso')
	if request.method == 'POST':
		# logging
		return HttpResponseRedirect('/thanks/')
