from groq import Groq
import os
import json

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analyze_idea(title, industry, description):

    prompt = f"""
You are a startup business analyst.

Analyze this startup idea.

Title: {title}
Industry: {industry}
Description: {description}

Return ONLY valid JSON.

Use concise business analysis.

{{
    "strengths":"2-3 short strengths",
    "weaknesses":"2-3 short weaknesses",
    "opportunities":"2-3 short opportunities",
    "threats":"2-3 short threats",
    "market":"Estimated market size and target market",
    "competitors":"Top 3 competitors",
    "score":"Viability score out of 10"
}}

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