from django.shortcuts import render
from .forms import IdeaForm
from .models import StartupIdea
from .ai_engine import analyze_idea
from django.http import FileResponse
from .pdf_generator import generate_pdf

def home(request):
    return render(request, 'home.html')

def idea_form(request):

    if request.method == 'POST':

        form = IdeaForm(request.POST)

        if form.is_valid():

            title = form.cleaned_data['title']
            industry = form.cleaned_data['industry']
            description = form.cleaned_data['description']
            problem = form.cleaned_data['problem']

            target_audience = form.cleaned_data[
                'target_audience'
           ]

            revenue_model = form.cleaned_data[
                'revenue_model'
            ]

            startup_stage = form.cleaned_data[
                'startup_stage'
            ]

            usp = form.cleaned_data['usp']

            startup_idea = StartupIdea(
                title=title,
                industry=industry,
                description=description,
                problem=problem,
                target_audience=target_audience,
                revenue_model=revenue_model,
                startup_stage=startup_stage,
                usp=usp
            )
            startup_idea.save()

            analysis = analyze_idea(
                title,
                industry,
                description,
                problem,
                target_audience,    
                revenue_model,
                startup_stage,
                usp
            )

            request.session[
                'report_data'
            ] = {

                'title': title,
                'industry': industry,
                'description': description,

                'analysis': analysis
            }

            return render(
                request,
                'loading.html',
                {
                    'next_url':
                    '/result/'
                }
            )

    else:

        form = IdeaForm()

    return render(
        request,
        'idea_form.html',
        {
            'form': form
        }
    )

def result_page(request):

    data = request.session.get(
        'report_data'
    )

    if not data:

        return render(
            request,
            'home.html'
        )

    return render(
        request,
        'result.html',
        {
            'title':
            data['title'],

            'industry':
            data['industry'],

            'description':
            data['description'],

            'analysis':
            data['analysis']
        }
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