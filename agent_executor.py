# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
    FilePart,
    FileWithBytes,
    FileWithUri,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.a2a.extension import try_activate_a2ui_extension

logger = logging.getLogger(__name__)

# --- Monkey-patch ADK to suppress mock_function_call_for_required_user_input ---
try:
  import google.adk.a2a.converters.to_adk_event as to_adk_event
  logger.info("--- Monkey-patching ADK _create_mock_function_call_for_required_user_input to be a no-op ---")
  to_adk_event._create_mock_function_call_for_required_user_input = lambda state, parts, ids: (parts, ids)
except Exception as e:
  logger.warning(f"--- Failed to monkey-patch ADK: {e} ---")


class PizzaAgentExecutor(AgentExecutor):
  """Slice & Rise Quality Agent Executor."""

  def __init__(self, agent):
    self._agent = agent

  async def execute(
      self,
      context: RequestContext,
      event_queue: EventQueue,
  ) -> None:
    query = ""
    ui_event_part = None
    action = None

    logger.info(f"--- PIZZA_EXECUTOR: Full incoming message: {context.message.model_dump() if context.message else None} ---")
    logger.info(f"--- PIZZA_EXECUTOR: Requested extensions: {context.requested_extensions} ---")
    active_ui_version = try_activate_a2ui_extension(context, self._agent.agent_card)

    if active_ui_version:
      logger.info(f"--- PIZZA_EXECUTOR: A2UI extension is active ({active_ui_version}). Using UI agent. ---")
    else:
      logger.info("--- PIZZA_EXECUTOR: A2UI extension is not active. Using text agent. ---")

    use_streaming = True
    form_user_input = None
    uploaded_image_bytes = None
    uploaded_image_mime = None

    if context.message and context.message.parts:
      for part in context.message.parts:
        if isinstance(part.root, DataPart):
          if "useStreaming" in part.root.data:
            use_streaming = part.root.data["useStreaming"]
          if part.root.data.get("version") == "v0.9" and "action" in part.root.data:
            ui_event_part = part.root.data["action"]
          elif "userAction" in part.root.data:
            ui_event_part = part.root.data["userAction"]
          if "user_input" in part.root.data:
            form_user_input = part.root.data["user_input"]
        elif isinstance(part.root, FilePart):
          file_obj = part.root.file
          if isinstance(file_obj, FileWithBytes):
            import base64
            uploaded_image_bytes = base64.b64decode(file_obj.bytes)
            uploaded_image_mime = file_obj.mime_type or "image/png"
            logger.info(f"--- PIZZA_EXECUTOR: Detected uploaded file in FilePart with bytes. Mime: {uploaded_image_mime}")
          elif isinstance(file_obj, FileWithUri):
            uploaded_image_mime = file_obj.mime_type or "image/png"
            logger.info(f"--- PIZZA_EXECUTOR: Detected uploaded file in FilePart with URI: {file_obj.uri}. Mime: {uploaded_image_mime}")

    if ui_event_part:
      logger.info(f"Received a2ui ClientEvent: {ui_event_part}")
      action = ui_event_part.get("name") or ui_event_part.get("actionName") or ""
      ctx = ui_event_part.get("context", {})
      if isinstance(ctx, list):
        # Convert A2UI context list of key-value maps to standard dictionary
        ctx_dict = {}
        for entry in ctx:
          k = entry.get("key")
          v = entry.get("value")
          if k is not None:
            ctx_dict[k] = v
        ctx = ctx_dict

      if action == "run_quality_audit":
        pizza_id = ctx.get("pizza_id") or ctx.get("pizzaId") or "perfect"
        query = f"Run standard quality audit for {pizza_id} pizza"
      elif action == "fetch_historical_trends":
        store_id = ctx.get("store_id") or "4021"
        query = f"Show me store {store_id} historical trends"
      elif action == "submit_correction":
        # Extract inputs from all possible places in A2UI ClientEvent structure
        inputs = ui_event_part.get("inputs") or ui_event_part.get("values") or {}
        if isinstance(inputs, list):
          inputs_dict = {}
          for item in inputs:
            if isinstance(item, dict) and "id" in item:
              inputs_dict[item["id"]] = item.get("value")
          inputs = inputs_dict
        
        # fallback to checking part.root.data directly for inputs
        if not inputs:
          inputs = {}
          if context.message and context.message.parts:
            for part in context.message.parts:
              if isinstance(part.root, DataPart):
                for k, v in part.root.data.items():
                  if k.startswith("input_") or k in ["height", "width", "volume", "top_color", "bottom_color"]:
                    inputs[k] = v
        
        # fallback to context
        for k, v in ctx.items():
          if k.startswith("input_") or k in ["height", "width", "volume", "top", "bottom"]:
            inputs[k] = v

        h = inputs.get("input_height") or inputs.get("height") or "0.90"
        w = inputs.get("input_width") or inputs.get("width") or "1.12"
        v = inputs.get("input_volume") or inputs.get("volume") or "0.44"
        tc = inputs.get("input_top_color") or inputs.get("top_color") or inputs.get("top") or "9"
        bc = inputs.get("input_bottom_color") or inputs.get("bottom_color") or inputs.get("bottom") or "8"
        scan_id = ctx.get("scan_id") or inputs.get("scan_id") or "scan_unknown"
        
        query = f"submit_correction_action scan_id={scan_id} height={h} width={w} volume={v} top={tc} bottom={bc}"
      elif action in ["verify_rating", "verify", "agree", "agree_rating"]:
        scan_id = ctx.get("scan_id") or "scan_unknown"
        query = f"verify_rating_action scan_id={scan_id}"
      else:
        query = f"User submitted action: {action} with context: {ctx}"
    else:
      query = context.get_user_input()

    if not query and form_user_input:
      query = form_user_input
      logger.info(f"--- PIZZA_EXECUTOR: Recovered query from form parameter: '{query}' ---")

    # If an image was uploaded, perform Gemini-driven multimodal analysis!
    if uploaded_image_bytes:
      logger.info("--- PIZZA_EXECUTOR: Performing multimodal classification on uploaded image ---")
      try:
        import os
        import json
        from google import genai
        from google.genai import types
        
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
        region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        client = genai.Client(vertexai=True, project=project_id, location=region)
        
        img_part = types.Part.from_bytes(
            data=uploaded_image_bytes,
            mime_type=uploaded_image_mime
        )
        
        prompt = (
            "You are an expert pizza quality control auditor for brand Slice & Rise. "
            "Analyze the uploaded pizza photograph and classify it into one of these three profiles:\n\n"
            "1. 'perfect': Beautiful golden leopard spotting, edge height 7/8\"-1\", edge width 1\"-1.25\", bottom mottled golden-brown.\n"
            "2. 'underbaked': Pale crust, flat doughy white edges, wide edge width, shallow center volume.\n"
            "3. 'burnt': Overly charred crust, charcoal blackened, burnt bottom, dried cheese.\n\n"
            "Return ONLY a JSON object in this format:\n"
            "{\n"
            "  \"pizza_type\": \"perfect\" | \"underbaked\" | \"burnt\"\n"
            "}"
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        res_data = json.loads(response.text)
        pizza_type = res_data.get("pizza_type", "perfect")
        logger.info(f"--- PIZZA_EXECUTOR: Multimodal auto-detected pizza type: {pizza_type} ---")
        
        # Override query to audit the auto-detected pizza profile
        query = f"Run standard quality audit for {pizza_type} pizza"
      except Exception as ex:
        logger.error(f"--- PIZZA_EXECUTOR: Error during multimodal classification: {ex} ---")

    logger.info(f"--- PIZZA_EXECUTOR: Final query for LLM: '{query}' ---")

    task = context.current_task
    if not task:
      task = new_task(context.message)
      await event_queue.enqueue_event(task)
    updater = TaskUpdater(event_queue, task.id, task.context_id)

    supported_catalogs = None
    if context.message and context.message.metadata:
      capabilities = context.message.metadata.get("a2uiClientCapabilities", {})
      if isinstance(capabilities, dict):
        supported_catalogs = capabilities.get("supportedCatalogIds", [])
        logger.info(f"--- PIZZA_EXECUTOR: client supportedCatalogIds: {supported_catalogs} ---")

    async for item in self._agent.stream(
        query,
        task.context_id,
        active_ui_version,
        use_streaming=use_streaming,
        supported_catalogs=supported_catalogs,
        uploaded_image_bytes=uploaded_image_bytes,
        uploaded_image_mime=uploaded_image_mime,
    ):
      is_task_complete = item["is_task_complete"]
      if not is_task_complete:
        message = None
        if "parts" in item:
          message = new_agent_parts_message(item["parts"], task.context_id, task.id)
        elif "updates" in item:
          message = new_agent_text_message(item["updates"], task.context_id, task.id)

        if message:
          await updater.update_status(TaskState.working, message)
        continue

      final_state = TaskState.completed

      message = None
      if "parts" in item:
        message = new_agent_parts_message(item["parts"], task.context_id, task.id)
      elif "updates" in item:
        message = new_agent_text_message(item["updates"], task.context_id, task.id)

      await updater.update_status(final_state, message)

  async def cancel(
      self, request: RequestContext, event_queue: EventQueue
  ) -> Task | None:
    raise ServerError(error=UnsupportedOperationError())
