from django.db import models

class StartupIdea(models.Model):

    title = models.CharField(
        max_length=200
    )

    industry = models.CharField(
        max_length=100
    )

    description = models.TextField()

    problem = models.TextField()

    target_audience = models.CharField(
        max_length=200
    )

    revenue_model = models.CharField(
        max_length=200
    )

    startup_stage = models.CharField(
        max_length=50
    )

    usp = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.title