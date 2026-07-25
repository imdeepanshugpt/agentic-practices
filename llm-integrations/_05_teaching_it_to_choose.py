"""Letting the model choose a tool for itself, via a tool schema.

Needs an OpenAI-compatible provider (Groq, OpenRouter, or OpenAI) --
Anthropic's tool-calling API uses a different response shape, covered
in a later module.

Setup: uv add openai python-dotenv
.env:  set at least one of GROQ_API_KEY / OPENROUTER_API_KEY / OPENAI_API_KEY
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()


SAMPLE_WEATHER = {
    "tokyo": {"celsius": 22, "conditions": "partly cloudy"},
    "delhi": {"celsius": 34, "conditions": "clear skies"},
    "london": {"celsius": 15, "conditions": "light rain"},
}


def get_weather(city: str) -> str:
    """Same tool as File 4 -- a plain function, unaware that an AI exists."""
    data = SAMPLE_WEATHER.get(city.lower())
    if data is None:
        return f"No weather data for {city!r}."
    return f"{city.title()}: {data['celsius']}C, {data['conditions']}"


# The "menu" handed to the model. It never sees get_weather() itself --
# only this description. The wording of "description" is what tells the
# model when this tool is relevant to a given question.
get_weather_schema = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city. Use this whenever "
                        "the user asks about weather, temperature, or conditions "
                        "in a specific place.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name, e.g. 'Tokyo'."}
            },
            "required": ["city"],
        },
    },
}

get_calculator_schema = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Use this tool to perform calculations. Use this whenever "
                        "the user asks for a calculation or a math problem.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The mathematical expression to calculate, e.g. '2 + 2'."}
            },
            "required": ["expression"],
        },
    },
}



def get_client_and_model():
    """Picks whichever OpenAI-compatible provider has a key set. Raises
    clearly if none is configured, since real decision-making genuinely
    needs a real model to call.
    """
    from openai import OpenAI

    if os.environ.get("GROQ_API_KEY"):
        return (
            OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1"),
            "llama-3.3-70b-versatile",
        )
    if os.environ.get("OPENROUTER_API_KEY"):
        return (
            OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1"),
            "openrouter/free",
        )
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"]), "gpt-4o-mini"

    raise RuntimeError(
        "No OpenAI-compatible key found. Set one of GROQ_API_KEY, "
        "OPENROUTER_API_KEY, or OPENAI_API_KEY in your .env file."
    )


def ask_ai_to_choose(question: str):
    """Sends the question plus the tool schema in one call. The reply may
    contain a tool_calls list instead of plain text -- that list is the
    model's decision, not an executed result.
    """
    client, model = get_client_and_model()
    response = client.chat.completions.create(
        model=model,
        max_tokens=300,
        messages=[{"role": "user", "content": question}],
        tools=[get_weather_schema, get_calculator_schema],
    )
    return response.choices[0].message


if __name__ == "__main__":
    question = "What is 2 times 2"
    message = ask_ai_to_choose(question)

    print(f"Model's raw reply: {message!r}")

    if message.tool_calls:
        call = message.tool_calls[0]
        # print('\n\n\n')
        # print(call)
        arguments = json.loads(call.function.arguments)
        # print('\n\n\n')
        # print(arguments, call.function.name)
        result = get_weather(**arguments)
        print(f"{call.function.name}({arguments}) -> {result}")
    else:
        print(message.content)



'''
Hi How are you

Model's raw reply: ChatCompletionMessage(content="I'm just a computer program, so I don't have feelings, but I'm here and ready to help you! How can I assist you today?", refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=None)


what is the weather like in Tokyo right now?

Model's raw reply: ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_x4l82uTQXd3UR6Nw4Nq8wy48', function=Function(arguments='{"city":"Tokyo"}', name='get_weather'), type='function')])

What is 2 times 2

Model's raw reply: ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_xOvtjwScctaVoFq3YIX8cwvn', function=Function(arguments='{"expression":"2 * 2"}', name='calculator'), type='function')])


'''


