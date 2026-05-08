from django.db import models


class OrderRecord(models.Model):
    """Placeholder relational model for future order replication."""

    reference = models.CharField(max_length=64)

    class Meta:
        managed = False

