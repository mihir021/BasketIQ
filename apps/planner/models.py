from django.db import models


class MealPlan(models.Model):
    """Placeholder relational model for future saved plans."""

    name = models.CharField(max_length=120)

    class Meta:
        managed = False

