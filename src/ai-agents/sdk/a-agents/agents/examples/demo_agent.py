import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from utils.call_agent_async.call_agent_async import call_agent_async

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


import warnings
warnings.filterwarnings("ignore")
import logging
logging.basicConfig(level=logging.ERROR)
print("Libraries imported.")


async def main():
    APP_NAME="app_1"
    USER_ID="moti_2323"
    SESSION_ID="ses-202"
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME,
                                                    user_id=USER_ID,
                                                    session_id=SESSION_ID
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
    root_agent = Agent(
        model='gemini-2.5-flash',
        name='root_agent',
        description=""Tells the current time in a specified city."",
        instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
        
    )

    print(f"Agent `root_agent`")


    runner = Runner(agent=root_agent,
                    app_name=APP_NAME,

                      session_service=session_service)
    await call_agent_async("What is the weather like in London?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)


    print(f"Runner created for agent '{runner.agent.name}'.")

