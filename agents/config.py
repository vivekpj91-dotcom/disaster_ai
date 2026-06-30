import os
import logging
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from agents.planner_agent import planner_agent

logger = logging.getLogger("disaster_assist.agents_config")

# Define Google ADK 2.0 Application
# Note: App name must match the agent directory name ('agents') or 'app' 
# to avoid session matching errors during testing/evals.
app = App(
    name="agents",
    root_agent=planner_agent
)

# Instantiate the Runner
# InMemoryRunner manages local session states, historical turns, and tool calls.
runner = InMemoryRunner(
    app=app
)

logger.info("Google ADK multi-agent Planner and Runner successfully initialized.")
