from groq import Groq
import os
import json

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analyze_idea(title, industry, description, problem, target_audience, revenue_model, startup_stage, usp):

    prompt = f"""
You are a startup business analyst.

Analyze this startup idea.

Title: {title}
Industry: {industry}
Description: {description}
Problem: {problem}
Target Audience: {target_audience}
Revenue Model: {revenue_model}
Startup Stage: {startup_stage}
USP: {usp}

Also provide:
- Practical startup improvement suggestions
- Recommended business model
- A short investor pitch summary
- Startup risk level with reasoning
- Estimated startup funding requirement

Return ONLY valid JSON.

Use concise business analysis.

{{
    "strengths":"2-3 short strengths",
    "weaknesses":"2-3 short weaknesses",
    "opportunities":"2-3 short opportunities",
    "threats":"2-3 short threats",
    "market":"Estimated market size and target market",
    "competitors":"Top 3 competitors",
    "score":"Viability score out of 10",
    "improvements":"Practical startup improvements",
    "business_model":"Suggested revenue/business model",
    "pitch":"Short investor pitch summary",
    "risk":"Startup risk level and reason",
    "funding":"Estimated startup funding requirement"
}}

Also estimate startup risk level
with short reasoning.
Rules:
- Only JSON
- No markdown
- No explanation
- Business focused
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response.choices[0].message.content

    print(result)   # DEBUG

    try:
        cleaned = (
            result
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        data = json.loads(cleaned)
        return data

    except Exception as e:

        print("JSON ERROR:", e)

        return {
            "strengths": result,
            "weaknesses": "Parsing failed",
            "opportunities": "",
            "threats": "",
            "market": "",
            "competitors": "",
            "score": "",
            "improvements": "",
            "business_model": "",
            "pitch": "",
            "risk": "",
            "funding": ""
        }