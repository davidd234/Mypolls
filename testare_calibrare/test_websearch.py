from openai import OpenAI
from secret_key import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

resp = client.responses.create(
    model="gpt-4o-mini",
    tools=[{"type": "web_search"}],
    input=[{"role": "user", "content": "Caută pe web cine este primarul Bucureștiului."}],
)

print(resp.output_text)
