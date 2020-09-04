from django.db import models
from Store.models import *

class StoreSync(models.Model):
    store = models.ForeignKey(
        'Store.Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    syncResponse = models.TextField(default="")
