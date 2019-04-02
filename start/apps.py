from django.apps import AppConfig
from start.models import Domains
from django.db.models.signals import post_save

from start.signals import save_domain


class StartConfig(AppConfig):
    name = 'start'

    # def ready(self):
    #    post_save.connect(save_domain, sender=Domains)
