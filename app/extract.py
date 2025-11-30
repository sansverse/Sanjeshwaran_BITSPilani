import json
import os
from groq import Groq
import re

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def clean_json_string(s: str):
    """
    Robust cleaning that finds the FIRST valid JSON object by counting braces.
    Ignores trailing garbage or repeated JSON blocks.
    """
    # 1. Basic cleanup
    s = s.replace("```json", "").replace("```", "").strip()

    # 2. Find the first opening brace
    start_index = s.find("{")
    if start_index == -1:
        raise ValueError("No JSON object start '{' found in LLM output")

    # 3. Count braces to find the matching closer
    # This handles nested JSON correctly
    brace_count = 0
    for i in range(start_index, len(s)):
        char = s[i]
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            
        # When count returns to 0, we found the closing brace of the main object
        if brace_count == 0:
            return s[start_index : i+1]

    # If we run out of string without closing, return what we have (it will likely fail, but better than nothing)
    return s[start_index:]


def extract_structured_data(ocr_text: str):
    messages = [
        {"role": "system", "content": """
You are an expert financial data extractor. Extract line items from medical bills into JSON.

### CRITICAL MATH & LOGIC RULES:
1. **Calculate Quantity from Rate:**
   - IF you see a Total Amount (e.g., 4500) and a Rate (e.g., 1500), YOU MUST CALCULATE Quantity = Amount / Rate (4500/1500 = 3).
   - DO NOT default to "item_quantity": 1 if the math implies otherwise.

2. **Handle Daily Charges & Repetitions:**
   - Extract EVERY single line item row-by-row.
   - If "Ward Charges" appears 5 times in the text, extract it 5 times.
   - If a service says "3 days" or "3 No", ensure item_quantity reflects that.

3. **Anti-Hallucination (Strict):**
   - NEVER extract a Date (e.g., "19/11/2025") as an item_amount.
   - NEVER extract a Batch Number (e.g., "30250779") as an item_amount.
   - NEVER extract Page Numbers (e.g., "Page 1 of 5") as quantities.
   - Exclude "Total", "Subtotal", "Balance Due", "Deposit" rows.

JSON FORMAT STRICTLY (No markdown, no code blocks):

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
"""},

        {"role": "user", "content": ocr_text}
    ]

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct", # Recommend using standard 70b if 'scout' is unstable
        messages=messages,
        temperature=0.1,
        # response_format={"type": "json_object"} # Uncomment if your model supports it!
    )

    llm_output = response.choices[0].message.content
    usage = response.usage

    # Clean & extract valid JSON
    json_str = clean_json_string(llm_output)

    try:
        parsed_json = json.loads(json_str)
    except Exception as e:
        print(f"FAILED JSON: {json_str}") # Print for debugging
        raise ValueError(f"LLM returned invalid JSON: {e}")

    return parsed_json, usage