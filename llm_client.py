from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
MODEL = "Qwen/Qwen2.5-72B-Instruct"

def call_structured(system: str, user: str, schema: type, temperature: float = 0.1) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
        response_format={"type": "json_object", "schema": schema.model_json_schema()},
        max_tokens=2048
    )
    return json.loads(response.choices[0].message.content)

def call_freeform(system: str, user: str, temperature: float = 0.2) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
        max_tokens=2048
    )
    return response.choices[0].message.content.strip()
