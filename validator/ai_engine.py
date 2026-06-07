from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

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
- TAM SAM SOM market breakdown
- 3 startup name suggestions
- A short startup tagline

Return ONLY valid JSON.

Use concise business analysis.

{{
    "strengths":"2-3 short strengths",
    "weaknesses":"2-3 short weaknesses",
    "opportunities":"2-3 short opportunities",
    "threats":"2-3 short threats",
    "market":"Estimated market size and target market",
    "competitors":[
    {{
        "name":"Competitor 1",
        "description":"Short description of competitor"
    }},
    {{
        "name":"Competitor 2",
        "description":"Short description of competitor"
    }},
    {{
        "name":"Competitor 3",
        "description":"Short description of competitor"
    }}
]
    "score":"Viability score out of 10",
    "improvements":"Practical startup improvements",
    "business_model":"Suggested revenue/business model",
    "pitch":"Short investor pitch summary",
    "risk":"Startup risk level and reason",
    "funding":"Estimated startup funding requirement",
    "tam_sam_som":{{
        "tam":"Estimated Total Addressable Market",
        "sam":"Estimated Serviceable Available Market",
        "som":"Estimated Serviceable Obtainable Market"
    }},

    "name_suggestions":"3 startup name suggestions",
    "tagline":"Short startup tagline"
}}


For competitors:
Return 3 real competitors relevant to the startup idea.
Each competitor must include:
- name
- short description of what they do


For tam_sam_som return an object, not a string.

Example:
"tam_sam_som":{{
    "tam":"$10 Billion",
    "sam":"$1 Billion",
    "som":"$100 Million"
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
            "score": ""
        }
    
    print("API KEY:", os.getenv("GROQ_API_KEY"))
    return {

            "score": "",
            "improvements": "",
            "business_model": "",
            "pitch": "",
            "risk": "",
            "funding": "",
            "tam_sam_som": "",
            "name_suggestions": "",
            "tagline": ""
        }
    

def compare_ideas(

    idea1,
    idea2
):

    prompt = f"""
You are a startup analyst.

Compare these startup ideas.

Analyze BOTH ideas separately first.

Then compare professionally.

Idea 1:
{idea1}

Idea 2:
{idea2}

Return ONLY valid JSON.
{{
    "winner":"Idea 1 or Idea 2",

    "idea1_strength":"2-3 strong points",
    "idea1_weakness":"2-3 weak points",
    "idea1_market":"Market opportunity and target users",
    "idea1_risk":"Execution and competition risks",
    "idea1_business":"Revenue and business model",

    "idea2_strength":"2-3 strong points",
    "idea2_weakness":"2-3 weak points",
    "idea2_market":"Market opportunity and target users",
    "idea2_risk":"Execution and competition risks",
    "idea2_business":"Revenue and business model",

    "comparison":"Professional startup comparison with clear reasoning",

    "recommendation":"Investor-style final recommendation"
}}
Rules:
- Only JSON
- No markdown
- Professional startup analysis
- Separate detailed analysis for both ideas
- Each field should contain 2-3 concise business points
- Clear and investor-style language
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    result = response.choices[
        0
    ].message.content

    cleaned = (
        result
        .replace("```json","")
        .replace("```","")
        .strip()
    )

    return json.loads(cleaned)

