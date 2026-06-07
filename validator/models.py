from django.db import models

from django.contrib.auth.models import User
# Create your models here.



class StartupIdea(models.Model):

    user = models.ForeignKey(
    User,
    on_delete=models.CASCADE
)

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

    # AI SAVED RESULTS

    strengths = models.TextField(
        blank=True,
        default=""
    )

    weaknesses = models.TextField(
        blank=True,
        default=""
    )

    opportunities = models.TextField(
        blank=True,
        default=""
    )

    threats = models.TextField(
        blank=True,
        default=""
    )

    market = models.TextField(
        blank=True,
        default=""
    )

    competitors = models.TextField(
        blank=True,
        default=""
    )

    score = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    improvements = models.TextField(
        blank=True,
        default=""
    )

    business_model = models.TextField(
        blank=True,
        default=""
    )

    pitch = models.TextField(
        blank=True,
        default=""
    )

    risk = models.TextField(
        blank=True,
        default=""
    )

    funding = models.TextField(
        blank=True,
        default=""
    )

    tam_sam_som = models.TextField(
        blank=True,
        default=""
    )

    name_suggestions = models.TextField(
        blank=True,
        default=""
    )

    tagline = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.title