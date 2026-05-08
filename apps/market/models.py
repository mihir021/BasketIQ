from django.db import models


class Category(models.Model):
    """Placeholder relational model for future catalogue expansion."""

    name = models.CharField(max_length=120, unique=True)

    class Meta:
        managed = False

