from django.shortcuts import render
from start.models import Domains

import logging
logger = logging.getLogger(__name__)


def index(request):
    # TODO! check if session has errors
    ds = Domains.objects.all()

    return render(request, 'index.html', {'domains': ds})
