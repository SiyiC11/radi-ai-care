import openai
from utils.prompt_template import get_prompt

def explain_report(report, language):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": get_prompt(language)},
            {"role": "user", "content": report}
        ],
        temperature=0.6
    )
    return response["choices"][0]["message"]["content"]
