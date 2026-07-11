
def ai_model(question: str) -> str:
  return f"[stub prediction for]: {question}"

class Chatbot:
  def __init__(self) -> None:
    self.history: list[dict] = []

  def ask(self, question:str) -> str:
    self.history.append({"role":"user", "content": question})
    answer = ai_model(question)
    self.history.append({"role":"assistant", "content": answer})
    return answer;

class Agent:
  def __init__(self, tools:dict[str, callable]) -> None:
    self.history: list[dict] = []
    self.tools = tools

  def decide_tool(self, question:str) -> str:
    for name in self.tools:
      if name in question.lower():
        return name
      return None

  def ask(self, question:str) -> str:
    self.history.append({ "role": "user", "content": question })
    tool_name = self.decide_tool(question)

    if tool_name is not None:
      result = self.tools[tool_name]()
      answer = f"used tool: {tool_name} {result}"
    else:
      answer = ai_model(question)

    self.history.append({ "role": "assistant", "content": answer})
    return answer





if __name__ == "__main__":
  def weather() -> str:
    return "22C, partly cloudy"

  chatbot = Chatbot()
  print(chatbot.ask("What is the capital of france ?"));

  agent = Agent(tools={"weather":weather})
  print(agent.ask("what's the weather like today"))
  print(agent.ask("what's capital of france"))



