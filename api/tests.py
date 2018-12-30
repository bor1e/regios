from django.test import TestCase
from start.models import Domains, Externals, Info
import json
import time


class ApiTestCase(TestCase):
    def setUp(self):
        d = Domains.objects.create(domain='medical-valley-emn.de',
                                   url='https://medical-valley-emn.de',
                                   status='finished')
        Info.objects.create(domain=d,
                            name='Medical Valley EMN e. V.',
                            zip=91052)
        Externals.objects.create(domain=d,
                                 url='http://d-hip.de')
        self.assertEqual(len(Domains.objects.all()), 1)

    def test_contains_medical(self):
        d = Domains.objects.get(domain='medical-valley-emn.de')
        self.assertEqual(d.domain, 'medical-valley-emn.de')

    def test_medical_has_external(self):
        d = Domains.objects.get(domain='medical-valley-emn.de')
        self.assertEqual(d.externals.count(), 1)

    def test_adding_domain(self):
        res = self.client.get('/display/medical-valley-emn.de')
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/display/check', {'url': 'http://d-hip.de'})
        self.assertEqual(Domains.objects.filter(domain='d-hip.de').count(), 1)
        self.assertEqual(len(Domains.objects.all()), 2)

    def test_starting_botspider(self):
        res = self.client.post('/api/post/', {'domain': 'd-hip.de',
                                              'url': 'http://d-hip.de',
                                              'name': 'botspider',
                                              'keywords': 'test_keywords'})
        self.assertEqual(Domains.objects.filter(domain='d-hip.de').count(), 1)
        self.assertEqual(len(Domains.objects.all()), 2)
        task_id = json.loads(res.content)['task_id']
        now = time.time()
        time.sleep(1)
        res = self.client.get('/api/scrapy_jobs_status/', {'timer': now})
        self.assertEqual(json.loads(res.content)['remaining'], 1)
        time.sleep(10)
        res = self.client.get('/api/get/', {'task_id': task_id,
                                            'domain': 'd-hip.de'})
        self.assertEqual(json.loads(res.content)['data']['status'], 'finished')
        # print(json.loads(res.content)['data'])
        # d = Domains.objects.get(domain='d-hip.de')
        # d_count = 7
        # self.assertEqual(d.locals.count(), d_count)

    def test_cancel_job(self):
        res = self.client.post('/api/post/', {'domain': 'd-hip.de',
                                              'url': 'http://d-hip.de',
                                              'name': 'botspider',
                                              'keywords': 'test_keywords'})
        task_id = json.loads(res.content)['task_id']
        now = time.time()
        res = self.client.get('/api/scrapy_jobs_status/', {'timer': now})
        self.assertEqual(json.loads(res.content)['remaining'], 1)
        res = self.client.get('/api/cancel_job/' + task_id)
        res = self.client.get('/api/scrapy_jobs_status/', {'timer': now})
        self.assertEqual(json.loads(res.content)['remaining'], 0)
