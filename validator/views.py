from django.shortcuts import render
from .forms import IdeaForm
from .models import StartupIdea
from .ai_engine import (analyze_idea, compare_ideas)
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

            startup_idea = StartupIdea(
                user=request.user,


                title=title,
                industry=industry,
                description=description,

                problem=problem,
                target_audience=target_audience,
                revenue_model=revenue_model,
                startup_stage=startup_stage,
                usp=usp,

                strengths=analysis['strengths'],
                weaknesses=analysis['weaknesses'],
                opportunities=analysis['opportunities'],
                threats=analysis['threats'],
                market=analysis['market'],
                competitors=analysis['competitors'],
                score=analysis['score'],

                improvements=analysis['improvements'],
                business_model=analysis['business_model'],
                pitch=analysis['pitch'],
                risk=analysis['risk'],
                funding=analysis['funding'],
                tam_sam_som=analysis['tam_sam_som'],
                name_suggestions=analysis['name_suggestions'],
                tagline=analysis['tagline']
            )

            startup_idea.save()

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

def compare_view(request):

    if request.method == 'POST':

        idea1 = request.POST.get(
            'idea1'
        )

        idea2 = request.POST.get(
            'idea2'
        )

        result = compare_ideas(
            idea1,
            idea2
        )

        return render(

            request,

            'compare_result.html',

            {
                'result': result,
                'idea1': idea1,
                'idea2': idea2
            }
        )

    return render(
        request,
        'compare.html'
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

def history_view(request):

    ideas = StartupIdea.objects.all().order_by(
        '-id'
    )

    return render(

        request,

        'history.html',

        {
            'ideas': ideas
        }
    )

def history_detail(

    request,
    idea_id
):

    idea = StartupIdea.objects.get(
        id=idea_id
    )

    analysis = {

    'strengths': idea.strengths,
    'weaknesses': idea.weaknesses,
    'opportunities': idea.opportunities,
    'threats': idea.threats,
    'market': idea.market,
    'competitors': idea.competitors,
    'score': idea.score,

    'improvements': idea.improvements,
    'business_model': idea.business_model,
    'pitch': idea.pitch,
    'risk': idea.risk,
    'funding': idea.funding,
    'tam_sam_som': idea.tam_sam_som,
    'name_suggestions': idea.name_suggestions,
    'tagline': idea.tagline
}

    return render(

        request,

        'result.html',

        {
            'title': idea.title,
            'industry': idea.industry,
            'description': idea.description,
            'analysis': analysis
        }
    )