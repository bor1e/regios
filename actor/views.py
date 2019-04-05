from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
from django.contrib import messages

from urllib.parse import urlparse
from start.models import Domains
# logger
import logging

logger = logging.getLogger(__name__)

"""
the domain in the backend is the actor in the frontend
actor == domain
"""


def index(request):
    return render(request, 'index_2.html')


# @login_required
def create(request):
    url = request.POST.get('url', request.COOKIES['url'])
    next = request.POST.get('next', '/')

    if not url:
        messages.error(request, 'URL is missing!')
        return redirect(next)

    domain = _get_domain_without_prefix_from_url(url)
    domain_db = Domains.objects.filter(domain__icontains=domain)

    if not domain_db.exists():
        # create
        obj = Domains.objects.create(domain=domain, url=url)
        msg = 'Domain: {} created'.format(obj.domain)
        logger.info(msg)
        return redirect('display_2', domain=obj.domain)
    else:
        obj = domain_db.first()
        if obj.status == 'finished':
            msg = 'Domain: {} already crawled.'.format(obj.domain)
            logger.info(msg)
            messages.info(request, msg)
            # TODO redirect either to network or to domain
            return redirect('/')
        else:
            msg = 'Domain: {} is being crawled.'.format(obj.domain)
            logger.info(msg)
            messages.info(request, msg)
            return redirect('display_2', domain=obj.domain)


'''
# signal when external finished
def start_info_scan(request, domain_name):
    try:
        domain = Domains.objects.get(domain=domain_name)
        # TODO keep it mind external scan only if external found!
        # --> if domain.externals.count == 0:
        # =====> domain.status = 'finished'
        # set it in spider update if len(externals) == 0 ...
        info_spider = _start_crawling(domain.domain, 'info')
        messages.info(request, 'spider {} for domain: {} started'
                      .format(info_spider, domain))

        # progress.html has to refresh all the time the domains.status
        # with possibility to cancel the crawling job
        return render(request, 'progress.html', {'domain': domain})
    except ObjectDoesNotExist:
        messages.error(request, 'domain {} does not exists.'
                       .format(domain_name))
        return redirect('return-back-to-where-coming-from')


def _start_crawling(domain_name, spider, *keywords):
    domain = Domains.objects.get(domain=domain_name)
    job_id = scrapyd.schedule('default', spider,
                              url=domain.url, domain=domain.domain,
                              keywords=keywords)
    domain.spider = Spiders.objects.create(domain=domain,
                                           name=spider,
                                           job_id=job_id)
    domain.status = spider + '_started'
    domain.save()
    return spider
    # -> redirect to progress.
    # --> i need a function which updates status
    # when finished update status of domain
    # start_info_scan_of_external_list after filtered domains
    # when finished update status of domain
    # set fullscan true
    # display
'''


def _get_domain_without_prefix_from_url(url):
    complete_domain = urlparse(url).netloc
    domain_split = complete_domain.split('.')
    common_prefixes = ['www', 'en', 'fr', 'de', 'er', ]

    while domain_split[0] in common_prefixes:
        domain_split = domain_split[1:]

    domain = '.'.join(domain_split)
    return domain
