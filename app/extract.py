import json
import os
from groq import Groq
import re

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def clean_json_string(s: str):
    """
    Removes backticks, markdown fences, and text outside the JSON object.
    Ensures only valid JSON is returned.
    """

    # Remove markdown code blocks
    s = s.replace("```json", "").replace("```", "").strip()

    # Extract JSON using regex (first {...} block)
    match = re.search(r"\{.*\}", s, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON object found in LLM output")

    json_str = match.group(0)

    return json_str


def extract_structured_data(ocr_text: str):
    messages = [
        {"role": "system", "content": """
You MUST return output ONLY in valid JSON. 
No explanations, no commentary, no code blocks.

JSON FORMAT STRICTLY:

{
  "pagewise_line_items": [
    {
      "page_no": "string",
      "page_type": "Bill Detail | Final Bill | Pharmacy",
      "bill_items": [
        {
          "item_name": "string",
          "item_amount": float,
          "item_rate": float,
          "item_quantity": float
        }
      ]
    }
  ],
  "total_item_count": integer
}

Do NOT invent fields. DO NOT include subtotal or final total.
"""},

        {"role": "user", "content": ocr_text}
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.1,
    )

    llm_output = response.choices[0].message.content
    usage = response.usage

    # Clean & extract valid JSON
    json_str = clean_json_string(llm_output)

    try:
        parsed_json = json.loads(json_str)
    except Exception as e:
        raise ValueError(f"LLM returned invalid JSON: {e}")

    return parsed_json, usage
