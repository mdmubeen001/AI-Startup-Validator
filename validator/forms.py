from django import forms
from .models import StartupIdea

class IdeaForm(forms.ModelForm):

    STARTUP_STAGE_CHOICES = [

        ('Idea', 'Idea'),

        ('Prototype', 'Prototype'),

        ('MVP', 'MVP'),

        ('Launched', 'Launched')

    ]

    startup_stage = forms.ChoiceField(
        choices=STARTUP_STAGE_CHOICES
    )

    class Meta:

        model = StartupIdea

        fields = [

            'title',
            'industry',
            'description',
            'problem',
            'target_audience',
            'revenue_model',
            'startup_stage',
            'usp'
        ]

        widgets = {

            'title':
            forms.TextInput(
                attrs={
                    'placeholder':
                    'Startup name'
                }
            ),

            'industry':
            forms.TextInput(
                attrs={
                    'placeholder':
                    'Fintech, Health, AI...'
                }
            ),

            'description':
            forms.Textarea(
                attrs={
                    'rows':4,
                    'placeholder':
                    'Describe your startup idea'
                }
            ),

            'problem':
            forms.Textarea(
                attrs={
                    'rows':3,
                    'placeholder':
                    'What problem are you solving?'
                }
            ),

            'target_audience':
            forms.TextInput(
                attrs={
                    'placeholder':
                    'Who are your customers?'
                }
            ),

            'revenue_model':
            forms.TextInput(
                attrs={
                    'placeholder':
                    'Subscription, Ads, Commission'
                }
            ),

            'usp':
            forms.Textarea(
                attrs={
                    'rows':3,
                    'placeholder':
                    'What makes your startup unique?'
                }
            )

        }