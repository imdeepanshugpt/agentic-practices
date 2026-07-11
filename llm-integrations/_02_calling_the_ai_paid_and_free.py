import os
import time

from dotenv import load_dotenv

load_dotenv()

def ask_groq(question: str) -> str:
  from openai import OpenAI
  start_time = time.perf_counter()
  print("Answering the question using Groq API....")
  client = OpenAI(api_key=os.environ["GROQ_API_KEY"],
  base_url = "https://api.groq.com/openai/v1")
  response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    max_tokens=200,
    messages=[{ "role": "user", "content": question}]
  )
  end_time = time.perf_counter()
  latency_ms = ( end_time - start_time ) * 1000
  print(f"token usages: prompt_tokens: {response.usage.prompt_tokens}, completion_tokens: {response.usage.completion_tokens}, latency: {latency_ms}")
  return response.choices[0].message.content

def ask_openrouter(question: str) -> str:
  from openai import OpenAI
  client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
  response = client.chat.completions.create(
    model="openrouter/free",
    max_tokens=200,
    messages=[{"role":"user", "content":question}]
  )
  return response.choices[0].message.content

def ask_anthropic(question: str) -> str:
  from anthropic import Anthropic
  client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
  response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=200,
    messages=[{"role": "user", "content": question}],
  )
  return response.content[0].text

def ask_openai(question: str) -> str:
  from openai import OpenAI

  client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
  response = client.chat.completions.create(
      model="gpt-4o-mini",
      max_tokens=200,
      messages=[{"role": "user", "content": question}],
  )

  print(response)
  return response.choices[0].message.content # 2024




def ask_ai(question: str) -> str:

  if os.environ.get("GROQ_API_KEY"):
    return ask_groq(question)
  if os.environ.get("OPENROUTER_API_KEY"):
    return ask_openrouter(question)
  if os.environ.get("OPENAI_API_KEY"):
    return ask_openai(question)
  if os.environ.get("ANTHROPIC_API_KEY"):
    return ask_anthropic(question)
  raise RuntimeError(
      "No API key found. Set one of GROQ_API_KEY, OPENROUTER_API_KEY, "
      "OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file."
  )


if __name__ == "__main__":
  question = "In One short sentence, what does ai agent do that a plain chatbot can't?"
  print(ask_ai(question))
