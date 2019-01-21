# from django.shortcuts import render, redirect, reverse
from start.models import Domains  # , BlackList
from django.http import HttpResponse, JsonResponse  # , HttpResponseRedirect
# from urllib.parse import urlparse
from django.views.decorators.csrf import csrf_exempt
# import json
import time
from datetime import datetime, timedelta
import logging
from scrapyd_api import ScrapydAPI
# connect scrapyd service
localhost = 'http://localhost:6800'
scrapyd = ScrapydAPI(localhost)

logger = logging.getLogger(__name__)


@csrf_exempt
def check_infoscan(request):
    domain = request.POST.get('domain')
    obj = Domains.objects.get(domain=domain)
    externals_list = [e.external_domain for e in obj.filtered_externals.all()]
    domains_list = [d.domain for d in Domains.objects.all()]
    for i in externals_list:
        if i not in domains_list:
            logger.info('{} is not infoscanned.'.format(i))
            return JsonResponse({'data': True})

    return JsonResponse({'data': False})


@csrf_exempt
def infoscan(request):
    domain = request.POST.get('domain')
    obj = Domains.objects.get(domain=domain)
    to_scan = obj.to_scan
    pre_jobs = scrapyd.list_jobs('default')
    pre_num = len(pre_jobs['pending']) + \
        len(pre_jobs['running']) + len(pre_jobs['finished'])
    remaining = to_scan.count()
    logger.debug('remaining: %s' % remaining)
    logger.debug('jobs: %s' % pre_num)
    now = time.time()
    for i in to_scan:
        logger.debug('creating domain: %s' % i.external_domain)
        external_domain_name = _remove_prefix(i.external_domain)
        if external_domain_name == 'd-hip.de':
            logger.debug('ALERT')
        if Domains.objects.filter(domain__icontains=external_domain_name).exists():
            if external_domain_name == 'd-hip.de':
                logger.debug('ALERT2')
            continue
        Domains.objects.create(domain=external_domain_name,
                               url=i.url, level=obj.level + 1,
                               src_domain=obj.domain)
        scrapyd.schedule('default', 'infospider',
                         url=i.url, domain=i.external_domain,
                         keywords=[])

    post_jobs = scrapyd.list_jobs('default')
    post_num = len(post_jobs['pending']) + \
        len(post_jobs['running']) + len(post_jobs['finished'])
    logger.debug('started jobs: %s' % (post_num - pre_num))
    if (post_num - pre_num) != remaining:
        logger.error('something went wrong by starting info scan')

    return JsonResponse({'remaining': remaining, 'time': now})


'''
# TODO probably I will need to extract this method into a single started, in
# order to be independet of the request.
# TODO should not render a website in api, rather return a JsonResponse
@csrf_exempt
def selected(request):
    selected = request.POST.getlist('selected')
        zip_from = request.POST.get('zip_from')
    zip_to = request.POST.get('zip_to')
    keywords = request.POST.get('keywords').strip().split(';')
    domains = Domains.objects.filter(info__zip__gte=zip_from).\
        exclude('info__zip__lte=zip_to')

    selected_domains = Domains.objects.filter(domain__in=selected)
    existing_domains = [d.pk for d in selected_domains if d.externals.exists()]
    domains = selected_domains.exclude(pk__in=existing_domains)
    jobs = {}
    now = time.time()
    for domain in domains:
        job_id = scrapyd.schedule('default', 'externalspider',
                                  url=domain.url,
                                  domain=domain.domain,
                                  keywords=[])
        jobs[domain.domain] = job_id
    # logger.debug('jobs: %s' % jobs)
    # TODO should render a website in api, rather a JsonResponse
    # return JsonResponse({'jobs': jobs})
    return render(request, 'selected.html', {'jobs': jobs,
                                             'timer': now})
    '''


def cancel_job(request, job_id):
    state = scrapyd.cancel('default', job_id)
    logger.debug('cancled while in state: %s' % state)
    return JsonResponse({'state': state})


@csrf_exempt
def scrapy_jobs_status(request):
    now = time.time()
    start = float(request.GET.get('timer'))
    duration = now - start
    elapsed = '{0}min {1:5.3f}sec'.format(int(duration / 60),
                                          float(duration % 60)),
    post_jobs = scrapyd.list_jobs('default')
    remaining = len(post_jobs['running']) + len(post_jobs['pending'])
    status = 'pending' if remaining > 0 else 'finished'
    return JsonResponse({'remaining': remaining, 'status': status,
                         'elapsed': elapsed})


@csrf_exempt
def get(request):
    task_id = request.GET.get('task_id', None)
    domain = request.GET.get('domain', None)
    logger.debug(u'%s' % domain)
    domain = domain.strip()
    if not task_id or not domain:
        return JsonResponse({'error': 'Missing args'})
    logger.debug('task_id: %s\ndomain: %s' % (task_id, domain))
    crawling = Domains.objects.get(domain=domain)
    logger.debug('domain to crawl: %s' % crawling)
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
                    start = datetime.strptime(
                        i['start_time'], '%Y-%m-%d %H:%M:%S.%f')
                    end = datetime.strptime(
                        i['end_time'], '%Y-%m-%d %H:%M:%S.%f')
                    duration = end - start
                    crawling.duration = duration
                    crawling.save()
                    duration = str(timedelta(seconds=duration.seconds))

            # log_placeholder = localhost + '/logs/default/crawler/{}.log'
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
                'duration': '{0}:{1:5.3f}'.format(int(duration / 60),
                                                  float(duration % 60)),
                # 'logs': log_placeholder.format(task_id),
            }
            return JsonResponse({'data': stats})
            # return render(request, 'home/status.html', stats)
        except Exception as e:
            # ! TODO error handling
            return JsonResponse({'error': str(e)})
    else:
        logger.info("STATUS : %s", status)
        if not status:
            status = 'not found/canceled'
        return JsonResponse({'status': status})

    # !TODO error handling
    return HttpResponse('ERROR')


@csrf_exempt
def post(request):
    spider = request.POST.dict()
    logger.debug('received spider params: %s', spider)
    domain_name = _remove_prefix(spider['domain'].strip())
    domain = Domains.objects.filter(domain__icontains=domain_name)
    url = ''
    if not domain.exists():
        domain = Domains.objects.create(domain=domain_name,
                                        url=spider['url'])
        url = spider['url']
        logger.debug('created domain: {}'.format(domain_name))
    else:
        logger.debug('found domain: {} status: {}'.
                     format(domain_name, domain.first().status))
        domain = domain.first()
        url = domain.url

    if domain.status == 'finished' and getattr(spider, 'job', '') == 'None' \
       or domain.fullscan:
        info = {
            'zip': domain.info.zip,
            'name': domain.info.name,
        }
        return JsonResponse({'info': info})

    task_id = scrapyd.schedule('default', spider['name'],
                               url=url, domain=spider['domain'],
                               keywords=spider['keywords'])

    return JsonResponse({'domain': spider['domain'],
                         'task_id': task_id,
                         'status': 'started'
                         })


def _remove_prefix(domain):
    domain_split = domain.split('.')
    # categorize domains matchmaking of words after skiping 'de','org','com'...
    common_prefixes = ['www', 'er', 'en', 'fr', 'de']
    if domain_split[0] in common_prefixes:
        return _remove_prefix('.'.join(domain_split[1:]))
    else:
        return domain
