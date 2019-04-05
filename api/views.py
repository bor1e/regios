# from django.shortcuts import render, redirect, reverse
from start.models import Domains, ExternalSpider, InfoSpider  # , BlackList
from django.http import HttpResponse, JsonResponse  # , HttpResponseRedirect
# from urllib.parse import urlparse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

# import json
import time
from datetime import datetime, timedelta
import logging
from scrapyd_api import ScrapydAPI
import requests

# connect scrapyd service
localhost = 'http://localhost:6800'
scrapyd = ScrapydAPI(localhost)

logger = logging.getLogger(__name__)


@csrf_exempt
def check_scrapy_running(request):
    # See [https://scrapyd.readthedocs.io/en/latest/api.html]
    # curl http://localhost:6800/daemonstatus.json
    try:
        data = requests.get(localhost + '/daemonstatus.json').json()
    except Exception:
        return JsonResponse({'data': 'error'}, status=503)

    return JsonResponse({'data': data})


@csrf_exempt
def check_infoscan(request):
    domain = request.POST.get('domain')
    obj = Domains.objects.get(domain=domain)
    externals_list = [e.external_domain for e in obj.filtered_externals.all()]
    for i in externals_list:
        if not Domains.objects.filter(domain__icontains=i):
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
        # for infoscan it is enough if subdomain was already once scaned
        if Domains.objects.filter(domain__icontains=i.external_domain)\
           .exists():
            remaining -= 1
            continue
        logger.debug('creating domain: %s' % i.external_domain)
        Domains.objects.create(domain=i.external_domain,
                               url=i.url, level=obj.level + 1,
                               src_domain=obj.domain)
        _start_spider(i.external_domain, 'infospider', [])

    post_jobs = scrapyd.list_jobs('default')
    post_num = len(post_jobs['pending']) + \
        len(post_jobs['running']) + len(post_jobs['finished'])
    logger.debug('started jobs: %s' % (post_num - pre_num))
    if (post_num - pre_num) != remaining:
        logger.error('something went wrong by starting info scan')

    logger.info('processing {} remainig domains.'.format(remaining))

    return JsonResponse({'remaining': remaining, 'time': now})


def cancel_job(request, job_id):
    domain = request.GET.get('domain', None)
    spider = request.GET.get('spider', None)
    if not (domain or spider):
        msg = 'No domain/spider information for job cancel'
        messages.warning(request, msg)
        logger.warning(msg)
        state = scrapyd.cancel('default', job_id)
        return JsonResponse({'state': state})

    '''
    # domain must exist, since passed on via backend, no user entrypoint
    obj = Domains.objects.get(domain=domain)
    if spider == 'external':
        if obj.has_external_spider():
            obj.externalspider.delete()
        obj.externalscan = False
        if obj.status == 'external_started':
            obj.status = 'created'
    elif spider == 'info':
        if obj.has_info_spider():
            obj.infospider.delete()
        obj.infoscan = False
        if obj.status == 'info_started':
            obj.status = 'created'
    obj.save()
    '''
    state = scrapyd.cancel('default', job_id)
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


# this is called while waiting for finish of spider external / info
def domain_spider_status(request):
    domain = request.POST.dict()['domain'].strip()
    spider = request.POST.dict()['spider'].strip()

    try:
        obj = Domains.objects.get(domain=domain)
        job_id = None
        if spider == 'external':
            job_id = obj.externalspider.job_id
        elif spider == 'info':
            job_id = obj.infospider.job_id
    except ObjectDoesNotExist:
        msg = 'Domain {} | Spider {} does not exist!'.format(domain, spider)
        logger.info(msg)
        return JsonResponse({'error': msg})

    status = scrapyd.job_status('default', job_id)
    if not status:
        status = 'not_found'
    logger.info('domain: {}, spider: {}, status: {}'.format(obj.domain,
                                                            spider, status))
    return JsonResponse({'domain': obj.domain,
                         'spider': spider,
                         'status': status
                         })


def start_info_crawl(request):
    domain = request.POST.dict()['domain'].strip()
    try:
        obj = Domains.objects.get(domain=domain)
        logger.debug('found domain: {} status: {}'.
                     format(domain, obj.status))
    except ObjectDoesNotExist:
        msg = 'Domain {} does not exist!'.format(domain)
        logger.info(msg)
        return JsonResponse({'error': msg})

    if len(obj.to_info_scan) == 0:
        msg = 'No info scan for Domain: {} to do!'.format(domain)
        logger.info(msg)
        return JsonResponse({'error': msg})

    # ENHANCEMENT: keywords could be an
    # attribute of network/domain => obj.keyword
    obj.status = 'info_started'
    obj.save()
    job_id = _start_spider(obj.domain, 'infospider', [])

    return JsonResponse({'domain': obj.domain,
                         'job_id': job_id,
                         'status': obj.status
                         })


def start_external_crawl(request):
    domain = request.POST.dict()['domain'].strip()
    try:
        obj = Domains.objects.get(domain=domain)
        logger.debug('found domain: {} status: {}'.
                     format(domain, obj.status))
    except ObjectDoesNotExist:
        msg = 'Domain {} does not exist!'.format(domain)
        logger.info(msg)
        return JsonResponse({'error': msg})

    if obj.has_external_spider():
        logger.debug('spider: {}'.format(obj.externalspider.unique_id))
        msg = 'Domain {} has already externals! Please refresh.'.format(domain)
        logger.info(msg)
        return JsonResponse({'error': msg})

    # ENHANCEMENT: keywords could be an
    # attribute of network/domain => obj.keyword
    obj.status = 'external_started'
    obj.save()
    job_id = _start_spider(obj.domain, 'externalspider', [])

    return JsonResponse({'domain': obj.domain,
                         'job_id': job_id,
                         'status': obj.status
                         })


@csrf_exempt
def post(request):
    spider = request.POST.dict()
    logger.debug('received spider params: %s', spider)
    domain_name = spider['domain'].strip()
    url = ''
    try:
        domain = Domains.objects.get(domain=domain_name)
        url = domain.url
        logger.debug('found domain: {} status: {}'.
                     format(domain_name, domain.status))
    except ObjectDoesNotExist:
        domain = Domains.objects.create(domain=domain_name,
                                        url=spider['url'])
        url = spider['url']
        logger.debug('created domain: {}'.format(domain_name))

    if domain.status == 'finished' and getattr(spider, 'job', '') == 'None' \
       or domain.fullscan:
        info = {
            'zip': domain.info.zip,
            'name': domain.info.name,
        }
        return JsonResponse({'info': info})

    # task_id = scrapyd.schedule('default', spider['name'],
    #                            url=url, domain=spider['domain'],
    #                            keywords=spider['keywords'])
    task_id = _start_spider(spider['domain'], spider['name'],
                            spider['keywords'])
    return JsonResponse({'domain': spider['domain'],
                         'task_id': task_id,
                         'status': 'started1'
                         })


def _start_spider(domain, spider, keywords):
    job_id = scrapyd.schedule('default', spider,
                              started_by_domain=domain,
                              keywords=keywords)
    obj = Domains.objects.get(domain=domain)
    if spider == 'externalspider':
        ExternalSpider.objects.create(domain=obj,
                                      job_id=job_id,
                                      to_scan=len(obj.to_external_scan))
    elif spider == 'infospider':
        InfoSpider.objects.create(domain=obj,
                                  job_id=job_id,
                                  to_scan=len(obj.to_info_scan))
    return job_id
