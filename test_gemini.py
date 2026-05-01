import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
response = client.models.generate_content(
    model="models/gemma-3-12b-it",
    contents="Reply with JSON: {status: replied, product_area: test, response: working, justification: test, request_type: invalid}",
    config=types.GenerateContentConfig(
        temperature=0
    )
)
print("API WORKS:", response.text)
