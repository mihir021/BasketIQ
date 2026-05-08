from django.db import models


class ExpenseReport(models.Model):
    """Placeholder relational model for future warehousing."""

    title = models.CharField(max_length=255)

    class Meta:
        managed = False

