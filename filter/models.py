from django.db import models
# from start.models import Domains


class BlackList(models.Model):
    ignore = models.TextField(max_length=200, unique=True)
    src_domain = models.TextField(max_length=200)
    # TODO brainstorming
    # ignore_only_for_src_domain =
    # models.BooleanField(null=True, default=False)

    def __str__(self):
        return self.ignore
