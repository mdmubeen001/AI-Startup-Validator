from django import forms

class IdeaForm(forms.Form):
    title = forms.CharField(
        max_length=100,
    )
    industry = forms.CharField(
        max_length=100,
    )

    description = forms.CharField(
        widget=forms.Textarea,
    )