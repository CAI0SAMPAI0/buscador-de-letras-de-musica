from dotenv import load_dotenv
from composio import Composio
from agents import Agent, Runner, SQLiteSession
from com import 

load_dotenv()

composio = Composio(provider=())

user_id = "user_123"
session = composio.sessions.create(user_id=user_id)
tools = session.tools()

agent = Agent(
    name="Personal Assistant",
    instructions=(
        "Use Composio tools to complete the request. "
        "If a connection is required, share its Connect Link and wait. "
        "Ask for confirmation before creating, updating, or deleting data."
    ),
    model="gpt-5.2",
    tools=tools,
)
# Memory for multi-turn conversation
memory = SQLiteSession("conversation")
print("""
What task would you like me to help you with?
I can use tools like Gmail, GitHub, Linear, Notion, and more.
(Type 'exit' to exit)
Example tasks:
  - 'Summarize my emails from today'
  - 'List all open issues on the composio github repository'
""")
while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        break
    print("Assistant: ", end="", flush=True)
    result = Runner.run_sync(starting_agent=agent, input=user_input, session=memory)
    print(f"{result.final_output}\n")