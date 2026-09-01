from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

if openrouter_api_key:
    print("OpenRouter API Key Loaded")
else:
    raise ValueError("OpenRouter API Key Not Found")

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

response = client.responses.create(
    model = "nvidia/nemotron-3.5-lightning:free",
    input = "What is our return policy?"
)
print(response.output_text)