from django.shortcuts import render
from .forms import IdeaForm
from .models import StartupIdea
from .ai_engine import analyze_idea
from django.http import FileResponse
from .pdf_generator import generate_pdf
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

@login_required
def idea_form(request):

    if request.method == 'POST':

        form = IdeaForm(request.POST)

        if form.is_valid():

            title = form.cleaned_data['title']
            industry = form.cleaned_data['industry']
            description = form.cleaned_data['description']

            # Save the idea to the database
            startup_idea = StartupIdea(
                user=request.user,
                title=title,
                industry=industry,
                description=description
            )
            startup_idea.save()

            # Analyze the idea
            analysis = analyze_idea(title, industry, description)

            request.session['report_data'] = {

    'title': title,
    'industry': industry,
    'description': description,

    'strengths':
    analysis['strengths'],

    'weaknesses':
    analysis['weaknesses'],

    'opportunities':
    analysis['opportunities'],

    'threats':
    analysis['threats'],

    'market':
    analysis['market'],

    'competitors':
    analysis['competitors'],

    'score':
    analysis['score']
}

            return render(
                request,
                'result.html',
                {
                    'title': title,
                    'industry': industry,
                    'description': description,
                    'analysis': analysis
                }
            )

    else:
        form = IdeaForm()

    return render(
        request,
        'idea_form.html',
        {'form': form}
    )


def download_pdf(request):

    data = request.session.get(
        'report_data'
    )

    filename = "media/report.pdf"

    generate_pdf(
        data,
        filename
    )

    return FileResponse(
        open(filename,'rb'),
        as_attachment=True
    )