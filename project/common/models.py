from django.db import models

from common.fields import UUIDField

class BaseModel(models.Model):
    id = UUIDField(primary_key=True, auto=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
