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


class CompareForm(forms.Form):
    first_title = forms.CharField(max_length=255, label='Startup Name')
    first_industry = forms.CharField(max_length=255, label='Industry')
    first_description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Description')
    first_problem = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Problem')
    first_revenue_model = forms.CharField(max_length=255, label='Revenue Model')
    first_usp = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Unique Value Proposition')
    
    second_title = forms.CharField(max_length=255, label='Startup Name')
    second_industry = forms.CharField(max_length=255, label='Industry')
    second_description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Description')
    second_problem = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Problem')
    second_revenue_model = forms.CharField(max_length=255, label='Revenue Model')
    second_usp = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Unique Value Proposition')