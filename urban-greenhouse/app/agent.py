# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.8-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from app.firestore_tools import (
    search_plants,
    get_plant_details,
    add_plant,
    log_watering_event,
    get_watering_history,
)
from app.weather_tool import get_ambient_plant_conditions
from app.maps_tools import geocode_address, find_nearby_places
from app.image_tool import generate_plant_image
from app.video_tool import generate_plant_video
from app.a2ui_utils import a2ui_callback
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog

# Read the Agent Engine resource name from deployment_metadata.json
_METADATA_FILE = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
_AGENT_ENGINE_RESOURCE_NAME = None
_MEMORY_BANK_ID = None
if os.path.exists(_METADATA_FILE):
    try:
        with open(_METADATA_FILE, "r") as f:
            _meta = json.load(f)
            _val = _meta.get("remote_agent_runtime_id")
            if _val and _val != "None":
                _AGENT_ENGINE_RESOURCE_NAME = _val
                _MEMORY_BANK_ID = _val.split("/")[-1]
    except Exception:
        pass

sandbox_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=_AGENT_ENGINE_RESOURCE_NAME
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for durable fact extraction."""
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        pass
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Urban Greenhouse botanical assistant. You help plant parents discover, "
        "care for, and maintain healthy indoor plants. You strictly remember and track all user allergies "
        "(such as pollen, mold, dust, latex/sap, pet sensitivities, toxicity concerns, and any specific plants "
        "or flowers the user or their household members are allergic to), preferences, and facts from previous conversations. "
        "Always use remembered allergies to ensure all plant recommendations, soil mixes, and care guidance are completely allergy-safe. "
        "You have access to a Firestore collection of greenhouse plants, with tools to search the plant catalog, "
        "view specific plant details, record new plants, and log/retrieve watering care events. When users ask about ambient climate, "
        "temperature, humidity, or seasonal weather for their plants in a given city, use the "
        "get_ambient_plant_conditions tool to provide real-time metrics and tailored plant advice. "
        "When users need to locate local plant nurseries, florists, botanical gardens, or garden centers, "
        "use geocode_address and find_nearby_places. "
        "When users want to see an image or visual preview of a plant or room setup, use generate_plant_image. "
        "When users want to see a video, timelapse, or animation of a plant, growth, or greenhouse scene, use generate_plant_video. "
        "When calculating plant fertilizer dosages, soil mix proportions, growth rates, lighting schedules, "
        "or data analysis, write and execute Python code using your secure code execution sandbox."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=sandbox_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        search_plants,
        get_plant_details,
        add_plant,
        log_watering_event,
        get_watering_history,
        get_ambient_plant_conditions,
        geocode_address,
        find_nearby_places,
        generate_plant_image,
        generate_plant_video,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)

