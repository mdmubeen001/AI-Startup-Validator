from django.shortcuts import render, redirect
from .forms import IdeaForm, CompareForm
from .models import StartupIdea
from .ai_engine import (analyze_idea, compare_ideas)
from django.http import FileResponse
from .pdf_generator import generate_pdf
from django.contrib.auth.decorators import login_required
import json

def home(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):

    ideas = StartupIdea.objects.filter(
        user=request.user
    ).order_by('-id')

    total_ideas = ideas.count()

    recent_ideas = ideas[:5]

    chart_labels = []
    chart_scores = []

    for idea in reversed(recent_ideas):
       chart_labels.append(idea.title)
       chart_scores.append(idea.score)

    last_idea = ideas.first()

    last_score = 0

    if last_idea and hasattr(last_idea, 'score'):
        last_score = last_idea.score

    average_score = 0

    if total_ideas > 0:
        average_score = sum(
            float(idea.score)
            for idea in ideas
            if idea.score
        ) / total_ideas

    context = {
        'total_ideas': total_ideas,
        'total_reports': total_ideas,
        'last_score': last_score,
        'average_score': round(average_score, 1),
        'recent_ideas': recent_ideas,
        'chart_labels': json.dumps(chart_labels),
        'chart_scores': json.dumps(chart_scores)
    }

    return render(
        request,
        'dashboard.html',
        context
    )


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

@login_required
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

@login_required
def compare_view(request):
    if request.method == 'POST':
        form = CompareForm(request.POST)
        if form.is_valid():
            # Format idea 1 data
            idea1 = f"""Startup Name: {form.cleaned_data['first_title']}
Industry: {form.cleaned_data['first_industry']}
Description: {form.cleaned_data['first_description']}
Problem: {form.cleaned_data['first_problem']}
Revenue Model: {form.cleaned_data['first_revenue_model']}
USP: {form.cleaned_data['first_usp']}"""
            
            # Format idea 2 data
            idea2 = f"""Startup Name: {form.cleaned_data['second_title']}
Industry: {form.cleaned_data['second_industry']}
Description: {form.cleaned_data['second_description']}
Problem: {form.cleaned_data['second_problem']}
Revenue Model: {form.cleaned_data['second_revenue_model']}
USP: {form.cleaned_data['second_usp']}"""
            
            result = compare_ideas(idea1, idea2)
            
            return render(
                request,
                'compare_result.html',
                {
                    'result': result,
                    'idea1': form.cleaned_data['first_title'],
                    'idea2': form.cleaned_data['second_title']
                }
            )
    else:
        form = CompareForm()
        
    return render(
        request,
        'compare.html',
        {'form': form}
    )

@login_required
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

@login_required
def history_view(request):

    ideas = StartupIdea.objects.filter(user=request.user).order_by(
        '-id'
    )

    return render(

        request,

        'history.html',

        {
            'ideas': ideas
        }
    )

@login_required
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


@login_required
def delete_idea(request, idea_id):
    if request.method == 'POST':
        idea = StartupIdea.objects.get(id=idea_id, user=request.user)
        idea.delete()
    return redirect('history')