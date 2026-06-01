from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(data, filename):

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    story = []

    title_style = styles['Title']
    heading = styles['Heading2']
    normal = styles['BodyText']

    story.append(
        Paragraph(
            "Startup Analysis Report",
            title_style
        )
    )

    story.append(
        Spacer(1,20)
    )

    story.append(
        Paragraph(
            f"<b>Startup:</b> {data['title']}",
            normal
        )
    )

    story.append(
        Paragraph(
            f"<b>Industry:</b> {data['industry']}",
            normal
        )
    )

    story.append(
        Paragraph(
            f"<b>Description:</b> {data['description']}",
            normal
        )
    )

    story.append(
        Spacer(1,20)
    )

    sections = [

        ("Strengths", data['strengths']),
        ("Weaknesses", data['weaknesses']),
        ("Opportunities", data['opportunities']),
        ("Threats", data['threats']),
        ("Market Size", data['market']),
        ("Competitors", data['competitors']),
        ("Viability Score", data['score'])
    ]

    for title, content in sections:

        story.append(
            Paragraph(
                title,
                heading
            )
        )

        story.append(
            Paragraph(
                str(content),
                normal
            )
        )

        story.append(
            Spacer(1,10)
        )

    doc.build(story)