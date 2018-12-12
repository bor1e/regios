from django.shortcuts import render, redirect, reverse
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


def multiple(request):
    return HttpResponse('multiple')


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
        if Domains.objects.filter(domain=i.external_domain).exists():
            continue
        Domains.objects.create(domain=i.external_domain,
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


@csrf_exempt
def infoscan_status(request):
    domain = request.GET.get('domain')
    logger.debug('domain: %s' % domain)
    now = time.time()
    start = request.GET.get('timer')
    elapsed = now - float(start)
    post_jobs = scrapyd.list_jobs('default')
    remaining = len(post_jobs['running']) + len(post_jobs['pending'])
    status = 'pending' if remaining > 0 else 'finished'
    return JsonResponse({'remaining': remaining, 'status': status,
                         'elapsed': elapsed})


@csrf_exempt
def get(request):
    task_id = request.GET.get('task_id', None)
    domain = request.GET.get('domain', None)
    if not task_id or not domain:
        return JsonResponse({'error': 'Missing args'})
    logger.debug('task_id: %s\ndomain: %s' % (task_id, domain))
    crawling = Domains.objects.get(domain=domain)
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

            log_placeholder = localhost + '/logs/default/crawler/{}.log'
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
                'logs': log_placeholder.format(task_id),
            }
            return JsonResponse({'data': stats})
            # return render(request, 'home/status.html', stats)
        except Exception as e:
            # ! TODO error handling
            return JsonResponse({'error': str(e)})
    else:
        logger.info("STATUS : %s", status)
        return JsonResponse({'status': status})

    # !TODO error handling
    return HttpResponse('ERROR')


@csrf_exempt
def post(request):
    spider = request.POST.dict()
    logger.debug('received spider params: %s', spider)

    domain = Domains.objects.filter(domain=spider['domain'])

    if not domain.exists():
        domain = Domains.objects.create(domain=spider['domain'],
                                        url=spider['url'])
        logger.debug('created domain: %s', spider['domain'])

    else:
        logger.debug('found domain: %s status: %s' %
                     (spider['domain'], domain.first().status))
        domain = domain.first()

    if domain.status == 'finished' and spider['job'] == 'None':
        info = {
            'zip': domain.info.zip,
            'name': domain.info.name
        }
        return JsonResponse({'info': info})

    task_id = scrapyd.schedule('default', spider['name'],
                               url=spider['url'], domain=spider['domain'],
                               keywords=spider['keywords'])

    return JsonResponse({'domain': spider['domain'],
                         'task_id': task_id,
                         'status': 'started'
                         })
