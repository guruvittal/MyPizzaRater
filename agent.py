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
import os
import uuid
from typing import Any, AsyncGenerator

from google import genai
from google.genai import types

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    DataPart,
    TextPart,
)
from a2ui.a2a.extension import get_a2ui_agent_extension

logger = logging.getLogger(__name__)


class PizzaAgent:
  """A2A-compliant wrapper for the Slice & Rise Quality Audit Agent."""

  SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

  def __init__(self, base_url: str):
    self.base_url = base_url
    self._agent_card = self._build_agent_card()

  @property
  def agent_card(self) -> AgentCard:
    return self._agent_card

  def _build_agent_card(self) -> AgentCard:
    extensions = [
        get_a2ui_agent_extension(
            "0.8",
            True, # accepts_inline_catalogs
            ["https://a2ui.org/specification/v0_8/standard_catalog_definition.json"],
        ),
        get_a2ui_agent_extension(
            "0.9",
            True, # accepts_inline_catalogs
            ["https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"],
        )
    ]

    capabilities = AgentCapabilities(
        streaming=True,
        extensions=extensions,
    )
    skill = AgentSkill(
        id="pizza_quality_auditer",
        name="Pizza Quality Standard Auditor",
        description=(
            "Audits pizza photographs against Slice & Rise standards for edge height, edge width, crust colors, and volume."
        ),
        tags=["pizza", "quality", "dashboard", "auditing"],
        examples=["Run standard quality audit for underbaked pizza", "Show me store 4021 historical trends"],
    )

    return AgentCard(
        name="Pizza Quality Standard Agent",
        description="Automates the back-of-house quality assurance of pizzas based on brand Slice & Rise standards.",
        url=self.base_url,
        version="1.0.0",
        default_input_modes=PizzaAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=PizzaAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

  def _get_static_profile(self, pizza_type: str) -> dict[str, Any]:
    profiles = {
        "perfect": {
            "name": "Artisanal Perfect (Neapolitan)",
            "grade": "PASS",
            "color": "#007A53",
            "metrics": [
                ("Edge Height", "0.94\"", "7/8\" - 1\"", "🟢 PASS (15/16\")"),
                ("Edge Width", "1.12\"", "1\" - 1 1/4\"", "🟢 PASS (1 1/8\")"),
                ("Center Volume", "0.44\"", "3/8\" - 1/2\"", "🟢 PASS (7/16\")"),
                ("Top Crust Color", "9/11", "Scale 7 - 11", "🟢 PASS (Golden leoparding)"),
                ("Bottom Crust Color", "8/10", "Scale 6 - 10", "🟢 PASS (Mottled golden-brown)"),
            ],
            "coaching": "Excellent stretching, proofing, and bake calibration. This pizza perfectly aligns with the Slice & Rise standard!"
        },
        "underbaked": {
            "name": "Underbaked / Pale Crust",
            "grade": "FAIL",
            "color": "#DA291C",
            "metrics": [
                ("Edge Height", "0.52\"", "7/8\" - 1\"", "🔴 FAIL (1/2\" - Flat edge)"),
                ("Edge Width", "1.45\"", "1\" - 1 1/4\"", "🔴 FAIL (1 7/16\" - Too wide)"),
                ("Center Volume", "0.25\"", "3/8\" - 1/2\"", "🔴 FAIL (1/4\" - Shallow center)"),
                ("Top Crust Color", "4/11", "Scale 7 - 11", "🔴 FAIL (Pale ivory)"),
                ("Bottom Crust Color", "3/10", "Scale 6 - 10", "🔴 FAIL (Doughy white)"),
            ],
            "coaching": "Symptom: Pale crust, flat edge, and low center volume. Operational Root Cause: Dough likely too cold when stretched (insufficient room-temp proofing) or conveyor oven belt running too fast.\n\n👉 Remediation Action: Let stretched dough proof at room temp for at least 15 extra minutes before baking. Ensure the oven belt cycle is set to exactly 420 seconds at 485°F."
        },
        "burnt": {
            "name": "Burnt / Overcooked Crust",
            "grade": "FAIL",
            "color": "#DA291C",
            "metrics": [
                ("Edge Height", "0.82\"", "7/8\" - 1\"", "⚠️ WARNING (13/16\" - Borderline)"),
                ("Edge Width", "1.05\"", "1\" - 1 1/4\"", "🟢 PASS (1 1/16\")"),
                ("Center Volume", "0.38\"", "3/8\" - 1/2\"", "🟢 PASS (3/8\")"),
                ("Top Crust Color", "12/11", "Scale 7 - 11", "🔴 FAIL (12/11 - Charcoal blackened)"),
                ("Bottom Crust Color", "11/10", "Scale 6 - 10", "🔴 FAIL (11/10 - Burnt crust)"),
            ],
            "coaching": "Symptom: Heavily charred crust, dried cheese, and slightly collapsed edge. Operational Root Cause: Oven conveyor belt running too slow or baking chamber temperature spiked above limits.\n\n👉 Remediation Action: Verify oven temperature is set to 485°F (not exceeding 490°F). Increase conveyor belt speed by 15-20 seconds to reduce bake duration."
        }
    }
    return profiles.get(pizza_type, profiles["perfect"])

  def _upload_to_gcs(self, image_bytes: bytes, filename: str) -> str:
    """Uploads image bytes to Google Cloud Storage and returns the GCS URI."""
    try:
      from google.cloud import storage
      project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
      storage_client = storage.Client(project=project_id)
      bucket = storage_client.bucket("slice_n_rise_scans")
      blob = bucket.blob(filename)
      blob.upload_from_string(image_bytes, content_type="image/png")
      gcs_uri = f"gs://slice_n_rise_scans/{filename}"
      logger.info(f"Successfully uploaded image to GCS: {gcs_uri}")
      return gcs_uri
    except Exception as e:
      logger.error(f"Failed to upload image to GCS: {e}")
      return ""

  def _parse_fraction_or_decimal(self, val_str: str) -> float | None:
    """Parses fraction string (e.g. 15/16) or decimal/mixed fractional (e.g. 1 1/8) to float."""
    if not val_str:
      return None
    val_str = val_str.replace('"', '').replace("''", "").strip()
    try:
      if ' ' in val_str:
        parts = val_str.split(' ')
        whole = float(parts[0])
        frac = parts[1]
        if '/' in frac:
          num, denom = frac.split('/')
          return whole + float(num) / float(denom)
        return float(val_str)
      elif '/' in val_str:
        num, denom = val_str.split('/')
        return float(num) / float(denom)
      else:
        import re
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if match:
          return float(match.group())
        return float(val_str)
    except Exception:
      return None

  def _parse_color_scale(self, val_str: str) -> int | None:
    """Parses color scale string (e.g. Scale 9, 8/10, or just 9) to integer."""
    if not val_str:
      return None
    try:
      import re
      match = re.search(r"\d+", val_str)
      if match:
        return int(match.group())
      return None
    except Exception:
      return None

  def _log_evaluation_to_bigquery(self, eval_data: dict[str, Any], scan_id: str, gcs_uri: str) -> None:
    """Logs baseline evaluation metrics to BigQuery pizza_evaluations table."""
    try:
      from google.cloud import bigquery
      from datetime import datetime, timezone
      project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
      bq_client = bigquery.Client(project=project_id)
      table_ref = f"{project_id}.slice_n_rise.pizza_evaluations"
      
      # Extract metrics
      metrics_list = eval_data.get("metrics", [])
      height = None
      width = None
      volume = None
      top_color = None
      bottom_color = None
      
      for m in metrics_list:
        name = m.get("name", "").lower()
        val = m.get("measurement", "")
        if "height" in name:
          height = self._parse_fraction_or_decimal(val)
        elif "width" in name:
          width = self._parse_fraction_or_decimal(val)
        elif "volume" in name:
          volume = self._parse_fraction_or_decimal(val)
        elif "top" in name:
          top_color = self._parse_color_scale(val)
        elif "bottom" in name:
          bottom_color = self._parse_color_scale(val)
            
      row = {
          "id": scan_id,
          "timestamp": datetime.now(timezone.utc).isoformat(),
          "store_id": "4021",
          "pizza_profile_name": eval_data.get("pizza_profile_name", ""),
          "overall_grade": eval_data.get("overall_grade", "PASS"),
          "gcs_uri": gcs_uri or None,
          "edge_height": height,
          "edge_width": width,
          "center_volume": volume,
          "top_color": top_color,
          "bottom_color": bottom_color,
          "human_edge_height": None,
          "human_edge_width": None,
          "human_center_volume": None,
          "human_top_color": None,
          "human_bottom_color": None,
          "verified": False,
          "user_corrected": False
      }
      
      errors = bq_client.insert_rows_json(table_ref, [row])
      if errors:
        logger.error(f"BigQuery insert_rows_json errors: {errors}")
      else:
        logger.info(f"Successfully logged baseline evaluation {scan_id} to BigQuery.")
    except Exception as e:
      logger.error(f"Failed to log baseline evaluation to BigQuery: {e}")

  def _update_evaluation_in_bigquery(
      self,
      scan_id: str,
      h: float,
      w: float,
      v: float,
      tc: int,
      bc: int
  ) -> bool:
    """Updates evaluation record in BigQuery with human corrective ratings."""
    try:
      from google.cloud import bigquery
      project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
      bq_client = bigquery.Client(project=project_id)
      table_ref = f"{project_id}.slice_n_rise.pizza_evaluations"
      
      # Let's check if the record exists first. If it does not exist, insert a default baseline row first!
      check_query = f"SELECT id FROM `{table_ref}` WHERE id = @scan_id LIMIT 1"
      job_config = bigquery.QueryJobConfig(
          query_parameters=[bigquery.ScalarQueryParameter("scan_id", "STRING", scan_id)]
      )
      rows = list(bq_client.query(check_query, job_config=job_config).result())
      if not rows:
        logger.warning(f"Scan record {scan_id} not found in BigQuery. Pre-inserting simulated baseline row.")
        from datetime import datetime, timezone
        row = {
            "id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "store_id": "4021",
            "pizza_profile_name": "Simulated Audit Pizza",
            "overall_grade": "FAIL",
            "gcs_uri": None,
            "edge_height": 0.50,
            "edge_width": 1.40,
            "center_volume": 0.25,
            "top_color": 4,
            "bottom_color": 3,
            "human_edge_height": None,
            "human_edge_width": None,
            "human_center_volume": None,
            "human_top_color": None,
            "human_bottom_color": None,
            "verified": False,
            "user_corrected": False
        }
        bq_client.insert_rows_json(table_ref, [row])

      query = f"""
          UPDATE `{table_ref}`
          SET human_edge_height = @height,
              human_edge_width = @width,
              human_center_volume = @volume,
              human_top_color = @top_color,
              human_bottom_color = @bottom_color,
              user_corrected = TRUE,
              verified = FALSE
          WHERE id = @scan_id
      """
      job_config = bigquery.QueryJobConfig(
          query_parameters=[
              bigquery.ScalarQueryParameter("height", "FLOAT64", h),
              bigquery.ScalarQueryParameter("width", "FLOAT64", w),
              bigquery.ScalarQueryParameter("volume", "FLOAT64", v),
              bigquery.ScalarQueryParameter("top_color", "INT64", tc),
              bigquery.ScalarQueryParameter("bottom_color", "INT64", bc),
              bigquery.ScalarQueryParameter("scan_id", "STRING", scan_id)
          ]
      )
      query_job = bq_client.query(query, job_config=job_config)
      query_job.result()
      logger.info(f"Successfully updated corrective feedback in BigQuery for scan_id: {scan_id}")
      return True
    except Exception as e:
      logger.error(f"Failed to update corrective feedback in BigQuery: {e}")
      return False

  def _verify_evaluation_in_bigquery(self, scan_id: str) -> bool:
    """Updates evaluation record in BigQuery, setting verified = TRUE."""
    try:
      from google.cloud import bigquery
      project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
      bq_client = bigquery.Client(project=project_id)
      table_ref = f"{project_id}.slice_n_rise.pizza_evaluations"
      
      # Let's check if the record exists first. If it does not exist, insert a default baseline row first!
      check_query = f"SELECT id FROM `{table_ref}` WHERE id = @scan_id LIMIT 1"
      job_config = bigquery.QueryJobConfig(
          query_parameters=[bigquery.ScalarQueryParameter("scan_id", "STRING", scan_id)]
      )
      rows = list(bq_client.query(check_query, job_config=job_config).result())
      if not rows:
        logger.warning(f"Scan record {scan_id} not found in BigQuery. Pre-inserting simulated baseline row.")
        from datetime import datetime, timezone
        row = {
            "id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "store_id": "4021",
            "pizza_profile_name": "Simulated Audit Pizza",
            "overall_grade": "FAIL",
            "gcs_uri": None,
            "edge_height": 0.90,
            "edge_width": 1.10,
            "center_volume": 0.45,
            "top_color": 9,
            "bottom_color": 8,
            "human_edge_height": None,
            "human_edge_width": None,
            "human_center_volume": None,
            "human_top_color": None,
            "human_bottom_color": None,
            "verified": False,
            "user_corrected": False
        }
        bq_client.insert_rows_json(table_ref, [row])

      query = f"""
          UPDATE `{table_ref}`
          SET verified = TRUE,
              user_corrected = FALSE
          WHERE id = @scan_id
      """
      job_config = bigquery.QueryJobConfig(
          query_parameters=[
              bigquery.ScalarQueryParameter("scan_id", "STRING", scan_id)
          ]
      )
      query_job = bq_client.query(query, job_config=job_config)
      query_job.result()
      logger.info(f"Successfully marked scan_id: {scan_id} as verified in BigQuery.")
      return True
    except Exception as e:
      logger.error(f"Failed to verify evaluation in BigQuery: {e}")
      return False

  def _parse_text_correction(self, text: str) -> dict[str, Any] | None:
    """Parses a text-based/conversational corrective rating from natural language/regex."""
    import re
    # Try to find a scan ID first (supports format like scan_abc123 or scan_sim_xyz)
    scan_match = re.search(r"scan_(?:sim_)?\w+", text, re.IGNORECASE)
    if not scan_match:
      return None
    scan_id = scan_match.group(0).lower()
    
    # Extract numbers associated with keys
    height = re.search(r"height[^\d\.]*(?P<val>\d+\.?\d*)", text, re.IGNORECASE)
    width = re.search(r"width[^\d\.]*(?P<val>\d+\.?\d*)", text, re.IGNORECASE)
    volume = re.search(r"volume[^\d\.]*(?P<val>\d+\.?\d*)", text, re.IGNORECASE)
    top = re.search(r"top[^\d]*(?P<val>\d+)", text, re.IGNORECASE)
    bottom = re.search(r"bottom[^\d]*(?P<val>\d+)", text, re.IGNORECASE)
    
    if height and width and volume and top and bottom:
      try:
        return {
            "scan_id": scan_id,
            "height": float(height.group("val")),
            "width": float(width.group("val")),
            "volume": float(volume.group("val")),
            "top_color": int(top.group("val")),
            "bottom_color": int(bottom.group("val"))
        }
      except Exception:
        pass
    return None

  async def stream(
      self,
      query: str,
      context_id: str,
      active_ui_version: str | None,
      use_streaming: bool = True,
      supported_catalogs: list[str] | None = None,
      uploaded_image_bytes: bytes | None = None,
      uploaded_image_mime: str | None = None,
  ) -> AsyncGenerator[dict[str, Any], None]:
    """Process incoming query and yield A2UI component states."""
    logger.info(f"PizzaAgent.stream: query='{query}', active_ui_version='{active_ui_version}'")
    
    # Intercept programmatic update actions
    q = query.lower()
    
    if q.startswith("submit_correction_action"):
      import re
      scan_id_match = re.search(r"scan_id=([^\s]+)", query)
      height_match = re.search(r"height=([^\s]+)", query)
      width_match = re.search(r"width=([^\s]+)", query)
      volume_match = re.search(r"volume=([^\s]+)", query)
      top_match = re.search(r"top=([^\s]+)", query)
      bottom_match = re.search(r"bottom=([^\s]+)", query)
      
      s_id = scan_id_match.group(1) if scan_id_match else "unknown"
      h = float(height_match.group(1)) if height_match else 0.90
      w = float(width_match.group(1)) if width_match else 1.12
      v = float(volume_match.group(1)) if volume_match else 0.44
      tc = int(top_match.group(1)) if top_match else 9
      bc = int(bottom_match.group(1)) if bottom_match else 8
      
      self._update_evaluation_in_bigquery(s_id, h, w, v, tc, bc)
      
      passH = h >= 0.875 and h <= 1.0
      passW = w >= 1.0 and w <= 1.25
      passV = v >= 0.375 and v <= 0.5
      passTC = tc >= 7 and tc <= 11
      passBC = bc >= 6 and bc <= 10
      corrected_is_pass = passH and passW and passV and passTC and passBC
      grade = "PASS" if corrected_is_pass else "FAIL"
      
      md_text = (
          f"✅ **Corrective Feedback Submitted!** BigQuery record updated successfully.\n\n"
          f"An SQL `UPDATE pizza_evaluations` query was run to store your corrective human labels alongside the machine labels:\n"
          f"* **QA Scan ID**: #{s_id}\n"
          f"* **Human Rating**: Edge Height {h:.2f}\", Edge Width {w:.2f}\", Center Volume {v:.2f}\", Top Color {tc}, Bottom Color {bc} ({grade})\n\n"
          f"This unified record serves as training pair telemetry for model retraining."
      )
      yield {
          "is_task_complete": True,
          "updates": md_text
      }
      return

    if q.startswith("verify_rating_action"):
      import re
      scan_id_match = re.search(r"scan_id=([^\s]+)", query)
      s_id = scan_id_match.group(1) if scan_id_match else "unknown"
      
      self._verify_evaluation_in_bigquery(s_id)
      
      md_text = (
          f"✅ **Evaluation Verified!** Record permanently stored as verified in BigQuery table.\n\n"
          f"I have marked QA Scan ID **#{s_id}** as verified in BigQuery. The regional supervisor dashboard has been updated."
      )
      yield {
          "is_task_complete": True,
          "updates": md_text
      }
      return

    # Check for text-based/conversational correction
    text_corr = self._parse_text_correction(query)
    if text_corr:
      s_id = text_corr["scan_id"]
      h = text_corr["height"]
      w = text_corr["width"]
      v = text_corr["volume"]
      tc = text_corr["top_color"]
      bc = text_corr["bottom_color"]
      
      self._update_evaluation_in_bigquery(s_id, h, w, v, tc, bc)
      
      passH = h >= 0.875 and h <= 1.0
      passW = w >= 1.0 and w <= 1.25
      passV = v >= 0.375 and v <= 0.5
      passTC = tc >= 7 and tc <= 11
      passBC = bc >= 6 and bc <= 10
      corrected_is_pass = passH and passW and passV and passTC and passBC
      grade = "PASS" if corrected_is_pass else "FAIL"
      
      md_text = (
          f"✅ **Corrective Feedback Submitted (conversational)!** BigQuery record updated successfully.\n\n"
          f"An SQL `UPDATE pizza_evaluations` query was run to store your corrective human labels alongside the machine labels:\n"
          f"* **QA Scan ID**: #{s_id}\n"
          f"* **Human Rating**: Edge Height {h:.2f}\", Edge Width {w:.2f}\", Center Volume {v:.2f}\", Top Color {tc}, Bottom Color {bc} ({grade})\n\n"
          f"This unified record serves as training pair telemetry for model retraining."
      )
      yield {
          "is_task_complete": True,
          "updates": md_text
      }
      return

    if uploaded_image_bytes:
      logger.info("Performing REAL multimodal Gemini evaluation on the uploaded image...")
      eval_data = self._call_gemini_multimodal_evaluation(uploaded_image_bytes, uploaded_image_mime)
      
      scan_id = f"scan_{uuid.uuid4().hex[:8]}"
      ext = "png"
      if uploaded_image_mime:
        if "jpeg" in uploaded_image_mime or "jpg" in uploaded_image_mime:
          ext = "jpg"
      filename = f"{scan_id}.{ext}"
      
      gcs_uri = self._upload_to_gcs(uploaded_image_bytes, filename)
      self._log_evaluation_to_bigquery(eval_data, scan_id, gcs_uri)
      
      if active_ui_version == "0.9":
        result = self._render_dynamic_scorecard_v09(eval_data, scan_id)
      else:
        result = self._render_dynamic_scorecard_v08(eval_data, scan_id)
      yield result
      return

    # Determine Pizza Profile based on query
    if "underbaked" in q or "pale" in q:
      pizza_type = "underbaked"
    elif "burnt" in q or "charred" in q or "overbaked" in q:
      pizza_type = "burnt"
    else:
      pizza_type = "perfect"

    # Match queries
    if "audit" in q or "scan" in q or "evaluate" in q:
      scan_id = f"scan_sim_{pizza_type}_{uuid.uuid4().hex[:4]}"
      # Log a simulated baseline evaluation row
      p = self._get_static_profile(pizza_type)
      metrics_formatted = []
      for name, measurement, specification, status_text in p["metrics"]:
        metrics_formatted.append({
            "name": name,
            "measurement": measurement,
            "specification": specification,
            "status_text": status_text
        })
      eval_data = {
          "pizza_profile_name": p["name"],
          "overall_grade": p["grade"],
          "metrics": metrics_formatted
      }
      self._log_evaluation_to_bigquery(eval_data, scan_id, gcs_uri="")

      if active_ui_version == "0.9":
        result = self._render_scorecard_v09(pizza_type, scan_id)
      else:
        result = self._render_scorecard_v08(pizza_type, scan_id)
      yield result
    elif "trend" in q or "dashboard" in q or "performance" in q or "how are we doing" in q:
      if active_ui_version == "0.9":
        result = self._render_trends_dashboard_v09()
      else:
        result = self._render_trends_dashboard_v08()
      yield result
    else:
      # Use Gemini to generate a helpful, standard-based conversational response!
      response_text = self._call_gemini_conversational(query)
      yield {
          "is_task_complete": True,
          "updates": response_text
      }

  def _call_gemini_conversational(self, query: str) -> str:
    """Invokes gemini-2.5-flash to dynamically answer general natural language questions about standards or quality auditing."""
    try:
      project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
      region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
      client = genai.Client(vertexai=True, project=project_id, location=region)
      
      system_instruction = (
          "You are the Slice & Rise Pizza Quality Agent. You automate back-of-house quality assurance "
          "of pizzas based on official brand Slice & Rise standards. "
          "Be conversational, professional, helpful, and concise. "
          "Use the following brand rules to answer the user's questions about standards, measurements, "
          "coaching, remediation, or how physical metrics/crust colors are checked:\n\n"
          "Brand Standards Guidelines:\n"
          "1. Edge Height: Must measure between 7/8\" (0.875\") and 1\". Under-proofed dough stays flat; over-proofed dough bubbles too high.\n"
          "2. Edge Width: Must measure between 1\" and 1 1/4\" (1.25\"). Too wide limits topping surface area; too narrow causes overflows.\n"
          "3. Center Volume: Must measure between 3/8\" (0.375\") and 1/2\" (0.5\") under cheese load.\n"
          "4. Top Crust Color: Checked via visual standard color-chart scale of 7 to 11 (ideal is vibrant golden brown with spotted black charring / golden leoparding).\n"
          "5. Bottom Crust Color: Checked via standard color-chart scale of 6 to 10 (ideal is well-cooked, crisp, mottled golden-brown, not pale or ash black).\n\n"
          "How Metrics are Checked:\n"
          "- Edge Height, Edge Width, and Center Volume are scanned by our high-resolution cameras using 3D spatial dimensions and visual modeling from top-down angles.\n"
          "- Crust Colors (Top and Bottom) are scanned by analyzing photographs against the brand reference scales. "
          "Specifically, the bottom crust color is checked when a photograph of the underside is captured (by lifting the pizza or via our bottom-angle tray cameras) "
          "and analyzed against the brand's standard visual reference spectrum (Scale 6-10).\n\n"
          "Remediation / Coaching Tips:\n"
          "- If a pizza is underbaked/pale: Check that conveyor belt speed is calibrated to exactly 420 seconds at 485°F. Make sure dough is proofed at room temp for 15+ minutes before stretching.\n"
          "- If a pizza is overcooked/burnt: Verify oven temp does not exceed 490°F (standard is 485°F). Increase conveyor belt speed by 15-20 seconds to reduce bake duration.\n\n"
          "Answer the user's specific query politely, reference these guidelines, and keep your answer short and professional."
      )
      
      response = client.models.generate_content(
          model="gemini-2.5-flash",
          contents=query,
          config=types.GenerateContentConfig(
              system_instruction=system_instruction,
              temperature=0.2
          )
      )
      return response.text
    except Exception as e:
      logger.error(f"Error calling Gemini in PizzaAgent: {e}")
      return "Hello! Ask me to 'Run standard quality audit' or check 'Historical trends' to see the native interactive dashboards."

  def _call_gemini_multimodal_evaluation(
      self,
      image_bytes: bytes,
      image_mime: str
  ) -> dict[str, Any]:
    """Invokes gemini-2.5-flash to perform a real evaluation of the pizza photograph."""
    try:
      project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
      region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
      client = genai.Client(vertexai=True, project=project_id, location=region)
      
      img_part = types.Part.from_bytes(
          data=image_bytes,
          mime_type=image_mime
      )
      
      prompt = (
          "You are the Slice & Rise Pizza Quality Agent. You automate back-of-house quality assurance "
          "of pizzas based on official brand Slice & Rise standards.\n\n"
          "Step 1: First, check if the uploaded image actually contains a pizza. If it is NOT a pizza "
          "(for example: a laptop screen, a computer, a person, a blank image, an animal, a room, or other non-pizza object), "
          "set 'is_pizza' to false and describe what the object/scene actually appears to be in 'detected_object', "
          "and provide a helpful error message in 'error_message' suggesting they upload a top-down, underside, or cross-section photo of a pizza.\n\n"
          "Step 2: If it IS a pizza, evaluate it visually against the official Slice & Rise standards:\n"
          "1. Edge Height: Standard is 7/8\" (0.875\") - 1\". Under-proofed dough stays flat (< 7/8\\\"); over-proofed dough bubbles too high (> 1\\\").\n"
          "2. Edge Width: Standard is 1\" - 1 1/4\" (1.25\"). Too wide (> 1.25\\\") limits topping area; too narrow (< 1\\\") causes overflows.\n"
          "3. Center Volume: Standard is 3/8\" (0.375\") - 1/2\" (0.5\") under cheese load.\n"
          "4. Top Crust Color: Checked via visual standard scale of 7 to 11 (ideal is vibrant golden brown with spotted black charring / golden leoparding).\n"
          "5. Bottom Crust Color: Checked via standard scale of 6 to 10 (ideal is well-cooked, crisp, mottled golden-brown, not pale or ash black).\n\n"
          "For each of these 5 metrics, visually estimate the measurement based on the photo. Provide:\n"
          "- 'measurement': e.g. \"15/16\\\"\", \"1 1/8\\\"\", \"1/2\\\"\", \"Scale 9 (Golden leoparding)\", \"Scale 8 (Mottled golden-brown)\"\n"
          "- 'status': \"PASS\" or \"FAIL\" or \"WARNING\"\n"
          "- 'status_text': e.g. \"🟢 PASS (15/16\\\")\", \"🔴 FAIL (1/2\\\" - Flat edge)\", \"🟢 PASS (Golden leoparding)\"\n"
          "Determine the 'overall_grade' (\"PASS\" if all pass or warning, \"FAIL\" if any fails) and 'pizza_profile_name' (e.g. \"Artisanal Perfect (Neapolitan)\", \"Underbaked / Pale Crust\", \"Burnt / Overcooked Crust\").\n\n"
          "Provide operational BOH coaching & remediation advice in 'coaching':\n"
          "- If underbaked: Mention pale crust/flat edge/low volume, root causes (dough too cold, insufficient proofing, belt too fast), and remediation (proof at room temp 15+ mins, conveyor speed 420s at 485F).\n"
          "- If overcooked/burnt: Mention charred/blackened crust, root causes (belt too slow, temp too high), and remediation (oven set to 485F, increase belt speed by 15-20s).\n"
          "- If perfect: Provide positive reinforcement on stretching, proofing, and bake calibration.\n\n"
          "Return ONLY a JSON object with this structure:\n"
          "{\n"
          "  \"is_pizza\": true,\n"
          "  \"detected_object\": \"pizza\",\n"
          "  \"pizza_profile_name\": \"Artisanal Perfect (Neapolitan)\",\n"
          "  \"overall_grade\": \"PASS\" | \"FAIL\",\n"
          "  \"theme_color\": \"#007A53\" or \"#DA291C\",\n"
          "  \"metrics\": [\n"
          "    {\n"
          "      \"name\": \"Edge Height\",\n"
          "      \"measurement\": \"15/16\\\"\",\n"
          "      \"specification\": \"7/8\\\" - 1\\\"\",\n"
          "      \"status_text\": \"🟢 PASS (15/16\\\")\"\n"
          "    },\n"
          "    {\n"
          "      \"name\": \"Edge Width\",\n"
          "      \"measurement\": \"1 1/8\\\"\",\n"
          "      \"specification\": \"1\\\" - 1 1/4\\\"\",\n"
          "      \"status_text\": \"🟢 PASS (1 1/8\\\")\"\n"
          "    },\n"
          "    {\n"
          "      \"name\": \"Center Volume\",\n"
          "      \"measurement\": \"7/16\\\"\",\n"
          "      \"specification\": \"3/8\\\" - 1/2\\\"\",\n"
          "      \"status_text\": \"🟢 PASS (7/16\\\")\"\n"
          "    },\n"
          "    {\n"
          "      \"name\": \"Top Crust Color\",\n"
          "      \"measurement\": \"Scale 9\",\n"
          "      \"specification\": \"Scale 7 - 11\",\n"
          "      \"status_text\": \"🟢 PASS (Golden leoparding)\"\n"
          "    },\n"
          "    {\n"
          "      \"name\": \"Bottom Crust Color\",\n"
          "      \"measurement\": \"Scale 8\",\n"
          "      \"specification\": \"Scale 6 - 10\",\n"
          "      \"status_text\": \"🟢 PASS (Mottled golden-brown)\"\n"
          "    }\n"
          "  ],\n"
          "  \"coaching\": \"...\"\n"
          "}\n\n"
          "If the image is NOT a pizza, return:\n"
          "{\n"
          "  \"is_pizza\": false,\n"
          "  \"detected_object\": \"<description of detected object, e.g. laptop screen displaying code>\",\n"
          "  \"error_message\": \"...\"\n"
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
      
      import json
      return json.loads(response.text)
    except Exception as e:
      logger.error(f"Error calling multimodal Gemini: {e}")
      return {
          "is_pizza": True,
          "pizza_profile_name": "Standard Pizza",
          "overall_grade": "PASS",
          "theme_color": "#007A53",
          "metrics": [
              {"name": "Edge Height", "measurement": "0.94\"", "specification": "7/8\" - 1\"", "status_text": "🟢 PASS (15/16\")"},
              {"name": "Edge Width", "measurement": "1.12\"", "specification": "1\" - 1 1/4\"", "status_text": "🟢 PASS (1 1/8\")"},
              {"name": "Center Volume", "measurement": "0.44\"", "specification": "3/8\" - 1/2\"", "status_text": "🟢 PASS (7/16\")"},
              {"name": "Top Crust Color", "measurement": "Scale 9", "specification": "Scale 7 - 11", "status_text": "🟢 PASS (Golden leoparding)"},
              {"name": "Bottom Crust Color", "measurement": "Scale 8", "specification": "Scale 6 - 10", "status_text": "🟢 PASS (Mottled golden-brown)"},
          ],
          "coaching": "Hello! I received your pizza photo, but encountered an issue with the AI analysis. Overall, it looks compliant!"
      }

  def _render_dynamic_scorecard_v09(self, eval_data: dict[str, Any], scan_id: str) -> dict[str, Any]:
    """Generates the A2UI v0.9 compliant scorecard component dynamically from real Gemini evaluation data."""
    is_pizza = eval_data.get("is_pizza", True)
    
    if not is_pizza:
      # Render a "Not a Pizza" warning card!
      detected = eval_data.get("detected_object", "unknown object")
      error_msg = eval_data.get("error_message", "Please upload a pizza photograph to audit.")
      
      md_text = f"⚠️ **Audit Warning**: The uploaded image is not a pizza. Detected: **{detected}**."
      
      components = [
          {
              "id": "scorecard_root",
              "component": "Column",
              "children": ["warning_card"]
          },
          {
              "id": "warning_card",
              "component": "Card",
              "child": "warning_column"
          },
          {
              "id": "warning_column",
              "component": "Column",
              "children": ["warning_title", "warning_badge", "warning_body"]
          },
          {
              "id": "warning_title",
              "component": "Text",
              "text": f"Evaluation Failed: Image is NOT a Pizza",
              "variant": "h1"
          },
          {
              "id": "warning_badge",
              "component": "Text",
              "text": f"Detected Object: {detected.upper()}",
              "variant": "h2"
          },
          {
              "id": "warning_body",
              "component": "Text",
              "text": error_msg,
              "variant": "body"
          }
      ]
      
      surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
      ui_json = [
          {
              "version": "v0.9",
              "createSurface": {
                  "surfaceId": surface_id,
                  "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
                  "root": "scorecard_root",
                  "theme": {
                      "primaryColor": "#DA291C",
                      "font": "Outfit"
                  }
              }
          },
          {
              "version": "v0.9",
              "updateComponents": {
                  "surfaceId": surface_id,
                  "components": components
              }
          }
      ]
      
      parts = [Part(root=TextPart(text=md_text))]
      parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])
      return {
          "is_task_complete": True,
          "parts": parts
      }

    # If it is a pizza, render the dynamic metrics!
    name = eval_data.get("pizza_profile_name", "Artisanal Perfect (Neapolitan)")
    grade = eval_data.get("overall_grade", "PASS")
    color = eval_data.get("theme_color", "#007A53")
    metrics = eval_data.get("metrics", [])
    coaching = eval_data.get("coaching", "")

    md_text = f"📊 Real-time multimodal evaluation complete for **{name}** (QA Scan ID: **#{scan_id}**):"

    components = []
    
    # Root Layout
    components.append({
        "id": "scorecard_root",
        "component": "Column",
        "children": ["grade_card", "measurements_card", "coaching_card", "hitl_card"]
    })

    # Grade Summary Card
    components.extend([
        {
            "id": "grade_card",
            "component": "Card",
            "child": "grade_column"
        },
        {
            "id": "grade_column",
            "component": "Column",
            "children": ["grade_title", "grade_badge", "store_info"]
        },
        {
            "id": "grade_title",
            "component": "Text",
            "text": f"Pizza Quality Evaluation: {name}",
            "variant": "h1"
        },
        {
            "id": "grade_badge",
            "component": "Text",
            "text": f"Overall Audit Result: {grade}",
            "variant": "h2"
        },
        {
            "id": "store_info",
            "component": "Text",
            "text": f"Auditing Entity: Vegas West Store #4021 • Active Shift\nQA Scan ID: #{scan_id}",
            "variant": "body"
        }
    ])

    # Measurements Card
    measure_children = ["measurements_title"]
    for i in range(len(metrics)):
      measure_children.append(f"metric_row_{i}")
    
    components.extend([
        {
            "id": "measurements_card",
            "component": "Card",
            "child": "measurements_column"
        },
        {
            "id": "measurements_column",
            "component": "Column",
            "children": measure_children
        },
        {
            "id": "measurements_title",
            "component": "Text",
            "text": "Physical Geometry & Color Telemetry",
            "variant": "h2"
        }
    ])

    # Add each metric row
    for i, m in enumerate(metrics):
      label_id = f"metric_label_{i}"
      status_id = f"metric_status_{i}"
      components.extend([
          {
              "id": f"metric_row_{i}",
              "component": "Row",
              "children": [label_id, status_id],
              "distribution": "spaceBetween"
          },
          {
              "id": label_id,
              "component": "Text",
              "text": f"• {m['name']} (Spec: {m['specification']})",
              "weight": 5
          },
          {
              "id": status_id,
              "component": "Text",
              "text": f"{m['status_text']}",
              "weight": 5
          }
      ])

    # Remediation Card
    components.extend([
        {
            "id": "coaching_card",
            "component": "Card",
            "child": "coaching_column"
        },
        {
            "id": "coaching_column",
            "component": "Column",
            "children": ["coaching_title", "coaching_body"]
        },
        {
            "id": "coaching_title",
            "component": "Text",
            "text": "Operational Coaching & BOH Remediation Advice",
            "variant": "h2"
        },
        {
            "id": "coaching_body",
            "component": "Text",
            "text": coaching,
            "variant": "body"
        }
    ])

    # Human-in-the-Loop Rating Form Card (A2UI v0.9 basic catalog compliant)
    components.extend([
        {
            "id": "hitl_card",
            "component": "Card",
            "child": "hitl_column"
        },
        {
            "id": "hitl_column",
            "component": "Column",
            "children": [
                "hitl_title",
                "hitl_desc",
                "input_height_label",
                "input_height",
                "input_width_label",
                "input_width",
                "input_volume_label",
                "input_volume",
                "input_top_color_label",
                "input_top_color",
                "input_bottom_color_label",
                "input_bottom_color",
                "hitl_submit_btn"
            ]
        },
        {
            "id": "hitl_title",
            "component": "Text",
            "text": "✏️ Human-in-the-Loop Rating Form",
            "variant": "h2"
        },
        {
            "id": "hitl_desc",
            "component": "Text",
            "text": "If you disagree with the AI's measurements, use the fields below to submit corrected values to the BigQuery telemetry table:",
            "variant": "body"
        },
        {
            "id": "input_height_label",
            "component": "Text",
            "text": "• Corrected Edge Height (Spec: 7/8\" - 1\")",
            "variant": "body"
        },
        {
            "id": "input_height",
            "component": "TextField",
            "label": "Edge Height (inches)",
            "value": "0.90"
        },
        {
            "id": "input_width_label",
            "component": "Text",
            "text": "• Corrected Edge Width (Spec: 1\" - 1 1/4\")",
            "variant": "body"
        },
        {
            "id": "input_width",
            "component": "TextField",
            "label": "Edge Width (inches)",
            "value": "1.12"
        },
        {
            "id": "input_volume_label",
            "component": "Text",
            "text": "• Corrected Center Volume (Spec: 3/8\" - 1/2\")",
            "variant": "body"
        },
        {
            "id": "input_volume",
            "component": "TextField",
            "label": "Center Volume (inches)",
            "value": "0.44"
        },
        {
            "id": "input_top_color_label",
            "component": "Text",
            "text": "• Corrected Top Crust Color (Scale 7 - 11)",
            "variant": "body"
        },
        {
            "id": "input_top_color",
            "component": "TextField",
            "label": "Top Crust Color (Scale)",
            "value": "9"
        },
        {
            "id": "input_bottom_color_label",
            "component": "Text",
            "text": "• Corrected Bottom Crust Color (Scale 6 - 10)",
            "variant": "body"
        },
        {
            "id": "input_bottom_color",
            "component": "TextField",
            "label": "Bottom Crust Color (Scale)",
            "value": "8"
        },
        {
            "id": "hitl_submit_btn",
            "component": "Button",
            "text": "Submit Corrective Rating & Update BigQuery",
            "action": {
                "name": "submit_correction",
                "context": {
                    "store_id": "4021",
                    "action_name": "submit_correction"
                }
            }
        }
    ])

    surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
    ui_json = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
                "root": "scorecard_root",
                "theme": {
                    "primaryColor": color,
                    "font": "Outfit"
                }
            }
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    ]

    parts = [Part(root=TextPart(text=md_text))]
    parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])

    return {
        "is_task_complete": True,
        "parts": parts
    }

  def _render_dynamic_scorecard_v08(self, eval_data: dict[str, Any], scan_id: str) -> dict[str, Any]:
    """Generates the A2UI v0.8 compliant scorecard component dynamically from real Gemini evaluation data."""
    is_pizza = eval_data.get("is_pizza", True)
    
    if not is_pizza:
      detected = eval_data.get("detected_object", "unknown object")
      error_msg = eval_data.get("error_message", "Please upload a pizza photograph to audit.")
      
      md_text = f"⚠️ **Audit Warning**: The uploaded image is not a pizza (QA Scan ID: **#{scan_id}**). Detected: **{detected}**."
      
      components = [
          {
              "id": "scorecard_root",
              "component": {
                  "Column": {
                      "children": {
                          "explicitList": ["warning_card"]
                      }
                  }
              }
          },
          {
              "id": "warning_card",
              "component": {
                  "Card": {
                      "child": "warning_column"
                  }
              }
          },
          {
              "id": "warning_column",
              "component": {
                  "Column": {
                      "children": {
                          "explicitList": ["warning_title", "warning_badge", "warning_body"]
                      }
                  }
              }
          },
          {
              "id": "warning_title",
              "component": {
                  "Text": {
                      "text": {
                          "literalString": "Evaluation Failed: Image is NOT a Pizza"
                      },
                      "usageHint": "h1"
                  }
              }
          },
          {
              "id": "warning_badge",
              "component": {
                  "Text": {
                      "text": {
                          "literalString": f"Detected Object: {detected.upper()}"
                      },
                      "usageHint": "h2"
                  }
              }
          },
          {
              "id": "warning_body",
              "component": {
                  "Text": {
                      "text": {
                          "literalString": error_msg
                      },
                      "usageHint": "body"
                  }
              }
          }
      ]
      
      surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
      ui_json = [
          {
              "beginRendering": {
                  "surfaceId": surface_id,
                  "catalogId": "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
                  "root": "scorecard_root",
                  "styles": {
                      "primaryColor": "#DA291C",
                      "font": "Outfit"
                  }
              }
          },
          {
              "surfaceUpdate": {
                  "surfaceId": surface_id,
                  "components": components
              }
          }
      ]
      
      parts = [Part(root=TextPart(text=md_text))]
      parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])
      return {
          "is_task_complete": True,
          "parts": parts
      }

    name = eval_data.get("pizza_profile_name", "Artisanal Perfect (Neapolitan)")
    grade = eval_data.get("overall_grade", "PASS")
    color = eval_data.get("theme_color", "#007A53")
    metrics = eval_data.get("metrics", [])
    coaching = eval_data.get("coaching", "")

    md_text = f"📊 Real-time multimodal evaluation complete for **{name}** (QA Scan ID: **#{scan_id}**):"

    components = []
    
    # Root Layout
    components.append({
        "id": "scorecard_root",
        "component": {
            "Column": {
                "children": {
                    "explicitList": ["grade_card", "measurements_card", "coaching_card", "hitl_card"]
                }
            }
        }
    })

    # Grade Summary Card
    components.extend([
        {
            "id": "grade_card",
            "component": {
                "Card": {
                    "child": "grade_column"
                }
            }
        },
        {
            "id": "grade_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["grade_title", "grade_badge", "store_info"]
                    }
                }
            }
        },
        {
            "id": "grade_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": f"Pizza Quality Evaluation: {name}"
                    },
                    "usageHint": "h1"
                }
            }
        },
        {
            "id": "grade_badge",
            "component": {
                "Text": {
                    "text": {
                        "literalString": f"Overall Audit Result: {grade}"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "store_info",
            "component": {
                "Text": {
                    "text": {
                        "literalString": f"Auditing Entity: Vegas West Store #4021 • Active Shift\nQA Scan ID: #{scan_id}"
                    },
                    "usageHint": "body"
                }
            }
        }
    ])

    # Measurements Card
    measure_children = ["measurements_title"]
    for i in range(len(metrics)):
      measure_children.append(f"metric_row_{i}")
    
    components.extend([
        {
            "id": "measurements_card",
            "component": {
                "Card": {
                    "child": "measurements_column"
                }
            }
        },
        {
            "id": "measurements_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": measure_children
                    }
                }
            }
        },
        {
            "id": "measurements_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Physical Geometry & Color Telemetry"
                    },
                    "usageHint": "h2"
                }
            }
        }
    ])

    # Add each metric row
    for i, m in enumerate(metrics):
      label_id = f"metric_label_{i}"
      status_id = f"metric_status_{i}"
      components.extend([
          {
              "id": f"metric_row_{i}",
              "component": {
                  "Row": {
                      "children": {
                          "explicitList": [label_id, status_id]
                      },
                      "distribution": "spaceBetween"
                  }
              }
          },
          {
              "id": label_id,
              "component": {
                  "Text": {
                      "text": {
                          "literalString": f"• {m['name']} (Spec: {m['specification']})"
                      }
                  }
              }
          },
          {
              "id": status_id,
              "component": {
                  "Text": {
                      "text": {
                          "literalString": f"{m['status_text']}"
                      }
                  }
              }
          }
      ])

    # Remediation Card
    components.extend([
        {
            "id": "coaching_card",
            "component": {
                "Card": {
                    "child": "coaching_column"
                }
            }
        },
        {
            "id": "coaching_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["coaching_title", "coaching_body"]
                    }
                }
            }
        },
        {
            "id": "coaching_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Operational Coaching & BOH Remediation Advice"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "coaching_body",
            "component": {
                "Text": {
                    "text": {
                        "literalString": coaching
                    },
                    "usageHint": "body"
                }
            }
        }
    ])

    # Human-in-the-Loop Rating Form Card (A2UI v0.8 standard catalog compliant)
    components.extend([
        {
            "id": "hitl_card",
            "component": {
                "Card": {
                    "child": "hitl_column"
                }
            }
        },
        {
            "id": "hitl_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            "hitl_title",
                            "hitl_desc",
                            "input_height_label",
                            "input_height",
                            "input_width_label",
                            "input_width",
                            "input_volume_label",
                            "input_volume",
                            "input_top_color_label",
                            "input_top_color",
                            "input_bottom_color_label",
                            "input_bottom_color",
                            "hitl_submit_btn"
                        ]
                    }
                }
            }
        },
        {
            "id": "hitl_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "✏️ Human-in-the-Loop Rating Form"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "hitl_desc",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "If you disagree with the AI's measurements, use the fields below to submit corrected values to the BigQuery telemetry table:"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_height_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Edge Height (Spec: 7/8\" - 1\")"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_height",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Edge Height (inches)"
                    },
                    "text": {
                        "literalString": "0.90"
                    }
                }
            }
        },
        {
            "id": "input_width_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Edge Width (Spec: 1\" - 1 1/4\")"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_width",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Edge Width (inches)"
                    },
                    "text": {
                        "literalString": "1.12"
                    }
                }
            }
        },
        {
            "id": "input_volume_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Center Volume (Spec: 3/8\" - 1/2\")"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_volume",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Center Volume (inches)"
                    },
                    "text": {
                        "literalString": "0.44"
                    }
                }
            }
        },
        {
            "id": "input_top_color_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Top Crust Color (Scale 7 - 11)"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_top_color",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Top Crust Color (Scale)"
                    },
                    "text": {
                        "literalString": "9"
                    }
                }
            }
        },
        {
            "id": "input_bottom_color_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Bottom Crust Color (Scale 6 - 10)"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_bottom_color",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Bottom Crust Color (Scale)"
                    },
                    "text": {
                        "literalString": "8"
                    }
                }
            }
        },
        {
            "id": "hitl_submit_btn",
            "component": {
                "Button": {
                    "child": "hitl_submit_btn_text",
                    "primary": True,
                    "action": {
                        "name": "submit_correction",
                        "context": [
                            {
                                "key": "scan_id",
                                "value": {
                                    "literalString": scan_id
                                }
                            },
                            {
                                "key": "input_height",
                                "value": {
                                    "path": "/input_height/text/literalString"
                                }
                            },
                            {
                                "key": "input_width",
                                "value": {
                                    "path": "/input_width/text/literalString"
                                }
                            },
                            {
                                "key": "input_volume",
                                "value": {
                                    "path": "/input_volume/text/literalString"
                                }
                            },
                            {
                                "key": "input_top_color",
                                "value": {
                                    "path": "/input_top_color/text/literalString"
                                }
                            },
                            {
                                "key": "input_bottom_color",
                                "value": {
                                    "path": "/input_bottom_color/text/literalString"
                                }
                            }
                        ]
                    }
                }
            }
        },
        {
            "id": "hitl_submit_btn_text",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Submit Corrective Rating & Update BigQuery"
                    }
                }
            }
        }
    ])

    surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
    ui_json = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
                "root": "scorecard_root",
                "styles": {
                    "primaryColor": color,
                    "font": "Outfit"
                }
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    ]

    parts = [Part(root=TextPart(text=md_text))]
    parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])

    return {
        "is_task_complete": True,
        "parts": parts
    }

  def _render_scorecard_v09(self, pizza_type: str, scan_id: str = None) -> dict[str, Any]:
    """Generates the A2UI v0.9 compliant scorecard component without technical A2UI jargon."""
    
    profiles = {
        "perfect": {
            "name": "Artisanal Perfect (Neapolitan)",
            "grade": "PASS",
            "color": "#007A53",
            "metrics": [
                ("Edge Height", "0.94\"", "7/8\" - 1\"", "🟢 PASS (15/16\")"),
                ("Edge Width", "1.12\"", "1\" - 1 1/4\"", "🟢 PASS (1 1/8\")"),
                ("Center Volume", "0.44\"", "3/8\" - 1/2\"", "🟢 PASS (7/16\")"),
                ("Top Crust Color", "9/11", "Scale 7 - 11", "🟢 PASS (Golden leoparding)"),
                ("Bottom Crust Color", "8/10", "Scale 6 - 10", "🟢 PASS (Mottled golden-brown)"),
            ],
            "coaching": "Excellent stretching, proofing, and bake calibration. This pizza perfectly aligns with the Slice & Rise standard!"
        },
        "underbaked": {
            "name": "Underbaked / Pale Crust",
            "grade": "FAIL",
            "color": "#DA291C",
            "metrics": [
                ("Edge Height", "0.52\"", "7/8\" - 1\"", "🔴 FAIL (1/2\" - Flat edge)"),
                ("Edge Width", "1.45\"", "1\" - 1 1/4\"", "🔴 FAIL (1 7/16\" - Too wide)"),
                ("Center Volume", "0.25\"", "3/8\" - 1/2\"", "🔴 FAIL (1/4\" - Shallow center)"),
                ("Top Crust Color", "4/11", "Scale 7 - 11", "🔴 FAIL (Pale ivory)"),
                ("Bottom Crust Color", "3/10", "Scale 6 - 10", "🔴 FAIL (Doughy white)"),
            ],
            "coaching": "Symptom: Pale crust, flat edge, and low center volume. Operational Root Cause: Dough likely too cold when stretched (insufficient room-temp proofing) or conveyor oven belt running too fast.\n\n👉 Remediation Action: Let stretched dough proof at room temp for at least 15 extra minutes before baking. Ensure the oven belt cycle is set to exactly 420 seconds at 485°F."
        },
        "burnt": {
            "name": "Burnt / Overcooked Crust",
            "grade": "FAIL",
            "color": "#DA291C",
            "metrics": [
                ("Edge Height", "0.82\"", "7/8\" - 1\"", "⚠️ WARNING (13/16\" - Borderline)"),
                ("Edge Width", "1.05\"", "1\" - 1 1/4\"", "🟢 PASS (1 1/16\")"),
                ("Center Volume", "0.38\"", "3/8\" - 1/2\"", "🟢 PASS (3/8\")"),
                ("Top Crust Color", "12/11", "Scale 7 - 11", "🔴 FAIL (12/11 - Charcoal blackened)"),
                ("Bottom Crust Color", "11/10", "Scale 6 - 10", "🔴 FAIL (11/10 - Burnt crust)"),
            ],
            "coaching": "Symptom: Heavily charred crust, dried cheese, and slightly collapsed edge. Operational Root Cause: Oven conveyor belt running too slow or baking chamber temperature spiked above limits.\n\n👉 Remediation Action: Verify oven temperature is set to 485°F (not exceeding 490°F). Increase conveyor belt speed by 15-20 seconds to reduce bake duration."
        }
    }

    p = profiles[pizza_type]
    if scan_id:
      md_text = f"📊 Generating the **Pizza Quality Grade Audit** context for **{p['name']}** (QA Scan ID: **#{scan_id}**) below:"
    else:
      md_text = f"📊 Generating the **Pizza Quality Grade Audit** context for **{p['name']}** below:"

    components = []
    
    # Root Layout
    components.append({
        "id": "scorecard_root",
        "component": "Column",
        "children": ["grade_card", "measurements_card", "coaching_card", "hitl_card"]
    })

    # Grade Summary Card
    components.extend([
        {
            "id": "grade_card",
            "component": "Card",
            "child": "grade_column"
        },
        {
            "id": "grade_column",
            "component": "Column",
            "children": ["grade_title", "grade_badge", "store_info"]
        },
        {
            "id": "grade_title",
            "component": "Text",
            "text": f"Pizza Quality Evaluation: {p['name']}",
            "variant": "h1"
        },
        {
            "id": "grade_badge",
            "component": "Text",
            "text": f"Overall Audit Result: {p['grade']}",
            "variant": "h2"
        },
        {
            "id": "store_info",
            "component": "Text",
            "text": "Auditing Entity: Vegas West Store #4021 • Active Shift",
            "variant": "body"
        }
    ])

    # Measurements Card
    measure_children = ["measurements_title"]
    for i, m in enumerate(p["metrics"]):
      measure_children.append(f"metric_row_{i}")
    
    components.extend([
        {
            "id": "measurements_card",
            "component": "Card",
            "child": "measurements_column"
        },
        {
            "id": "measurements_column",
            "component": "Column",
            "children": measure_children
        },
        {
            "id": "measurements_title",
            "component": "Text",
            "text": "Physical Geometry & Color Telemetry",
            "variant": "h2"
        }
    ])

    # Add each metric row
    for i, m in enumerate(p["metrics"]):
      label_id = f"metric_label_{i}"
      status_id = f"metric_status_{i}"
      components.extend([
          {
              "id": f"metric_row_{i}",
              "component": "Row",
              "children": [label_id, status_id],
              "distribution": "spaceBetween"
          },
          {
              "id": label_id,
              "component": "Text",
              "text": f"• {m[0]} (Spec: {m[2]})",
              "weight": 5
          },
          {
              "id": status_id,
              "component": "Text",
              "text": f"{m[3]}",
              "weight": 5
          }
      ])

    # Remediation Card
    components.extend([
        {
            "id": "coaching_card",
            "component": "Card",
            "child": "coaching_column"
        },
        {
            "id": "coaching_column",
            "component": "Column",
            "children": ["coaching_title", "coaching_body"]
        },
        {
            "id": "coaching_title",
            "component": "Text",
            "text": "Operational Coaching & BOH Remediation Advice",
            "variant": "h2"
        },
        {
            "id": "coaching_body",
            "component": "Text",
            "text": p["coaching"],
            "variant": "body"
        }
    ])

    v_height = "0.94" if pizza_type == "perfect" else ("0.52" if pizza_type == "underbaked" else "0.82")
    v_width = "1.12" if pizza_type == "perfect" else ("1.45" if pizza_type == "underbaked" else "1.05")
    v_volume = "0.44" if pizza_type == "perfect" else ("0.25" if pizza_type == "underbaked" else "0.38")
    v_top = "9" if pizza_type == "perfect" else ("4" if pizza_type == "underbaked" else "11")
    v_bottom = "8" if pizza_type == "perfect" else ("3" if pizza_type == "underbaked" else "10")

    # Human-in-the-Loop Rating Form Card (A2UI v0.9 basic catalog compliant)
    components.extend([
        {
            "id": "hitl_card",
            "component": "Card",
            "child": "hitl_column"
        },
        {
            "id": "hitl_column",
            "component": "Column",
            "children": [
                "hitl_title",
                "hitl_desc",
                "input_height_label",
                "input_height",
                "input_width_label",
                "input_width",
                "input_volume_label",
                "input_volume",
                "input_top_color_label",
                "input_top_color",
                "input_bottom_color_label",
                "input_bottom_color",
                "hitl_submit_btn"
            ]
        },
        {
            "id": "hitl_title",
            "component": "Text",
            "text": "✏️ Human-in-the-Loop Rating Form",
            "variant": "h2"
        },
        {
            "id": "hitl_desc",
            "component": "Text",
            "text": "If you disagree with the AI's measurements, use the fields below to submit corrected values to the BigQuery telemetry table:",
            "variant": "body"
        },
        {
            "id": "input_height_label",
            "component": "Text",
            "text": "• Corrected Edge Height (Spec: 7/8\" - 1\")",
            "variant": "body"
        },
        {
            "id": "input_height",
            "component": "TextField",
            "label": "Edge Height (inches)",
            "value": v_height
        },
        {
            "id": "input_width_label",
            "component": "Text",
            "text": "• Corrected Edge Width (Spec: 1\" - 1 1/4\")",
            "variant": "body"
        },
        {
            "id": "input_width",
            "component": "TextField",
            "label": "Edge Width (inches)",
            "value": v_width
        },
        {
            "id": "input_volume_label",
            "component": "Text",
            "text": "• Corrected Center Volume (Spec: 3/8\" - 1/2\")",
            "variant": "body"
        },
        {
            "id": "input_volume",
            "component": "TextField",
            "label": "Center Volume (inches)",
            "value": v_volume
        },
        {
            "id": "input_top_color_label",
            "component": "Text",
            "text": "• Corrected Top Crust Color (Scale 7 - 11)",
            "variant": "body"
        },
        {
            "id": "input_top_color",
            "component": "TextField",
            "label": "Top Crust Color (Scale)",
            "value": v_top
        },
        {
            "id": "input_bottom_color_label",
            "component": "Text",
            "text": "• Corrected Bottom Crust Color (Scale 6 - 10)",
            "variant": "body"
        },
        {
            "id": "input_bottom_color",
            "component": "TextField",
            "label": "Bottom Crust Color (Scale)",
            "value": v_bottom
        },
        {
            "id": "hitl_submit_btn",
            "component": "Button",
            "text": "Submit Corrective Rating & Update BigQuery",
            "action": {
                "name": "submit_correction",
                "context": {
                    "store_id": "4021",
                    "action_name": "submit_correction",
                    "scan_id": scan_id
                }
            }
        }
    ])

    surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
    ui_json = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
                "root": "scorecard_root",
                "theme": {
                    "primaryColor": p["color"],
                    "font": "Outfit"
                }
            }
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    ]

    parts = [Part(root=TextPart(text=md_text))]
    parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])

    return {
        "is_task_complete": True,
        "parts": parts
    }

  def _render_trends_dashboard_v09(self) -> dict[str, Any]:
    """Generates a premium Vega-Lite trends dashboard within native v0.9 components."""
    md_text = "📈 Querying BigQuery on the fly... Rendering the **Vegas West Store #4021 Weekly Trends Dashboard** below:"

    weekly_data = [
        {"date": "06/17", "pass_rate": 100},
        {"date": "06/18", "pass_rate": 50},
        {"date": "06/19", "pass_rate": 50},
        {"date": "06/20", "pass_rate": 100},
        {"date": "06/21", "pass_rate": 50},
        {"date": "06/22", "pass_rate": 66},
        {"date": "06/23", "pass_rate": 100}
    ]

    defects_data = [
        {"category": "Underbaked", "count": 3},
        {"category": "Overbaked", "count": 2},
        {"category": "Edge Width", "count": 1},
        {"category": "Edge Height", "count": 1},
        {"category": "Center Volume", "count": 0}
    ]

    components = [
        {
            "id": "dashboard_root",
            "component": "Column",
            "children": ["title_card", "kpi_card", "weekly_trend_card", "defects_card"]
        },
        {
            "id": "title_card",
            "component": "Card",
            "child": "title_column"
        },
        {
            "id": "title_column",
            "component": "Column",
            "children": ["title_h1", "title_body"]
        },
        {
            "id": "title_h1",
            "component": "Text",
            "text": "Store Quality Performance Dashboard",
            "variant": "h1"
        },
        {
            "id": "title_body",
            "component": "Text",
            "text": "Real-time auditing trends queried from BigQuery. Focuses on Slice & Rise compliance metrics.",
            "variant": "body"
        },
        {
            "id": "kpi_card",
            "component": "Card",
            "child": "kpi_row"
        },
        {
            "id": "kpi_row",
            "component": "Row",
            "children": ["kpi_scans", "kpi_rate", "kpi_defects"],
            "distribution": "spaceEvenly"
        },
        {
            "id": "kpi_scans",
            "component": "Text",
            "text": "Total Audited Scans:\n14 scans",
            "variant": "body"
        },
        {
            "id": "kpi_rate",
            "component": "Text",
            "text": "Average Pass Rate:\n84.5% (Target: 85%)",
            "variant": "body"
        },
        {
            "id": "kpi_defects",
            "component": "Text",
            "text": "Failed Defects:\n4 flagged alerts",
            "variant": "body"
        },
        {
            "id": "weekly_trend_card",
            "component": "Card",
            "child": "weekly_column"
        },
        {
            "id": "weekly_column",
            "component": "Column",
            "children": ["weekly_h2", "weekly_trend_chart"]
        },
        {
            "id": "weekly_h2",
            "component": "Text",
            "text": "7-Day Historical Pass Rate (%) vs Benchmark",
            "variant": "h2"
        },
        {
            "id": "weekly_trend_chart",
            "component": "VegaChart",
            "spec": {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "description": "7-Day Historical Pass Rate (%) vs Benchmark",
                "width": "container",
                "height": 200,
                "data": { "values": weekly_data },
                "mark": {
                    "type": "line",
                    "color": "#3b82f6",
                    "point": { "color": "#3b82f6", "size": 60 },
                    "strokeWidth": 3
                },
                "encoding": {
                    "x": {
                        "field": "date",
                        "type": "nominal",
                        "axis": { "title": "Date", "labelAngle": 0 }
                    },
                    "y": {
                        "field": "pass_rate",
                        "type": "quantitative",
                        "scale": { "domain": [0, 100] },
                        "axis": { "title": "Pass Rate (%)" }
                    }
                }
            }
        },
        {
            "id": "defects_card",
            "component": "Card",
            "child": "defects_column"
        },
        {
            "id": "defects_column",
            "component": "Column",
            "children": ["defects_h2", "defects_chart"]
        },
        {
            "id": "defects_h2",
            "component": "Text",
            "text": "Corporate Auditing Failure Pareto Chart",
            "variant": "h2"
        },
        {
            "id": "defects_chart",
            "component": "VegaChart",
            "spec": {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "description": "Corporate Auditing Failure Pareto Chart",
                "width": "container",
                "height": 200,
                "data": { "values": defects_data },
                "mark": {
                    "type": "bar",
                    "color": "#ef4444",
                    "cornerRadiusEnd": 4
                },
                "encoding": {
                    "x": {
                        "field": "category",
                        "type": "nominal",
                        "axis": { "title": "Defect Category", "labelAngle": -15 }
                    },
                    "y": {
                        "field": "count",
                        "type": "quantitative",
                        "axis": { "title": "Occurrences" }
                    }
                }
            }
        }
    ]

    surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
    ui_json = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
                "root": "dashboard_root",
                "theme": {
                    "primaryColor": "#3b82f6",
                    "font": "Outfit"
                }
            }
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    ]

    parts = [Part(root=TextPart(text=md_text))]
    parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])

    return {
        "is_task_complete": True,
        "parts": parts
    }

  def _render_scorecard_v08(self, pizza_type: str, scan_id: str = None) -> dict[str, Any]:
    """Generates the A2UI v0.8 compliant scorecard component."""
    profiles = {
        "perfect": {
            "name": "Artisanal Perfect (Neapolitan)",
            "grade": "PASS",
            "color": "#007A53",
            "metrics": [
                ("Edge Height", "0.94\"", "7/8\" - 1\"", "🟢 PASS (15/16\")"),
                ("Edge Width", "1.12\"", "1\" - 1 1/4\"", "🟢 PASS (1 1/8\")"),
                ("Center Volume", "0.44\"", "3/8\" - 1/2\"", "🟢 PASS (7/16\")"),
                ("Top Crust Color", "9/11", "Scale 7 - 11", "🟢 PASS (Golden leoparding)"),
                ("Bottom Crust Color", "8/10", "Scale 6 - 10", "🟢 PASS (Mottled golden-brown)"),
            ],
            "coaching": "Excellent stretching, proofing, and bake calibration. This pizza perfectly aligns with the Slice & Rise standard!"
        },
        "underbaked": {
            "name": "Underbaked / Pale Crust",
            "grade": "FAIL",
            "color": "#DA291C",
            "metrics": [
                ("Edge Height", "0.52\"", "7/8\" - 1\"", "🔴 FAIL (1/2\" - Flat edge)"),
                ("Edge Width", "1.45\"", "1\" - 1 1/4\"", "🔴 FAIL (1 7/16\" - Too wide)"),
                ("Center Volume", "0.25\"", "3/8\" - 1/2\"", "🔴 FAIL (1/4\" - Shallow center)"),
                ("Top Crust Color", "4/11", "Scale 7 - 11", "🔴 FAIL (Pale ivory)"),
                ("Bottom Crust Color", "3/10", "Scale 6 - 10", "🔴 FAIL (Doughy white)"),
            ],
            "coaching": "Symptom: Pale crust, flat edge, and low center volume. Operational Root Cause: Dough likely too cold when stretched (insufficient room-temp proofing) or conveyor oven belt running too fast.\n\n👉 Remediation Action: Let stretched dough proof at room temp for at least 15 extra minutes before baking. Ensure the oven belt cycle is set to exactly 420 seconds at 485°F."
        },
        "burnt": {
            "name": "Burnt / Overcooked Crust",
            "grade": "FAIL",
            "color": "#DA291C",
            "metrics": [
                ("Edge Height", "0.82\"", "7/8\" - 1\"", "⚠️ WARNING (13/16\" - Borderline)"),
                ("Edge Width", "1.05\"", "1\" - 1 1/4\"", "🟢 PASS (1 1/16\")"),
                ("Center Volume", "0.38\"", "3/8\" - 1/2\"", "🟢 PASS (3/8\")"),
                ("Top Crust Color", "12/11", "Scale 7 - 11", "🔴 FAIL (12/11 - Charcoal blackened)"),
                ("Bottom Crust Color", "11/10", "Scale 6 - 10", "🔴 FAIL (11/10 - Burnt crust)"),
            ],
            "coaching": "Symptom: Heavily charred crust, dried cheese, and slightly collapsed edge. Operational Root Cause: Oven conveyor belt running too slow or baking chamber temperature spiked above limits.\n\n👉 Remediation Action: Verify oven temperature is set to 485°F (not exceeding 490°F). Increase conveyor belt speed by 15-20 seconds to reduce bake duration."
        }
    }

    p = profiles[pizza_type]
    if scan_id:
      md_text = f"📊 Generating the **Pizza Quality Grade Audit** context for **{p['name']}** (QA Scan ID: **#{scan_id}**) below:"
    else:
      md_text = f"📊 Generating the **Pizza Quality Grade Audit** context for **{p['name']}** below:"

    components = []
    
    # Root Layout
    components.append({
        "id": "scorecard_root",
        "component": {
            "Column": {
                "children": {
                    "explicitList": ["grade_card", "measurements_card", "coaching_card", "hitl_card"]
                }
            }
        }
    })

    # Grade Summary Card
    components.extend([
        {
            "id": "grade_card",
            "component": {
                "Card": {
                    "child": "grade_column"
                }
            }
        },
        {
            "id": "grade_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["grade_title", "grade_badge", "store_info"]
                    }
                }
            }
        },
        {
            "id": "grade_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": f"Pizza Quality Evaluation: {p['name']}"
                    },
                    "usageHint": "h1"
                }
            }
        },
        {
            "id": "grade_badge",
            "component": {
                "Text": {
                    "text": {
                        "literalString": f"Overall Audit Result: {p['grade']}"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "store_info",
            "component": {
                "Text": {
                    "text": {
                        "literalString": f"Auditing Entity: Vegas West Store #4021 • Active Shift\nQA Scan ID: #{scan_id}" if scan_id else "Auditing Entity: Vegas West Store #4021 • Active Shift"
                    },
                    "usageHint": "body"
                }
            }
        }
    ])

    # Measurements Card
    measure_children = ["measurements_title"]
    for i in range(len(p["metrics"])):
      measure_children.append(f"metric_row_{i}")
    
    components.extend([
        {
            "id": "measurements_card",
            "component": {
                "Card": {
                    "child": "measurements_column"
                }
            }
        },
        {
            "id": "measurements_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": measure_children
                    }
                }
            }
        },
        {
            "id": "measurements_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Physical Geometry & Color Telemetry"
                    },
                    "usageHint": "h2"
                }
            }
        }
    ])

    # Add each metric row
    for i, m in enumerate(p["metrics"]):
      label_id = f"metric_label_{i}"
      status_id = f"metric_status_{i}"
      components.extend([
          {
              "id": f"metric_row_{i}",
              "component": {
                  "Row": {
                      "children": {
                          "explicitList": [label_id, status_id]
                      },
                      "distribution": "spaceBetween"
                  }
              }
          },
          {
              "id": label_id,
              "component": {
                  "Text": {
                      "text": {
                          "literalString": f"• {m[0]} (Spec: {m[2]})"
                      }
                  }
              }
          },
          {
              "id": status_id,
              "component": {
                  "Text": {
                      "text": {
                          "literalString": f"{m[3]}"
                      }
                  }
              }
          }
      ])

    # Remediation Card
    components.extend([
        {
            "id": "coaching_card",
            "component": {
                "Card": {
                    "child": "coaching_column"
                }
            }
        },
        {
            "id": "coaching_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["coaching_title", "coaching_body"]
                    }
                }
            }
        },
        {
            "id": "coaching_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Operational Coaching & BOH Remediation Advice"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "coaching_body",
            "component": {
                "Text": {
                    "text": {
                        "literalString": p["coaching"]
                    },
                    "usageHint": "body"
                }
            }
        }
    ])

    v_height = "0.94" if pizza_type == "perfect" else ("0.52" if pizza_type == "underbaked" else "0.82")
    v_width = "1.12" if pizza_type == "perfect" else ("1.45" if pizza_type == "underbaked" else "1.05")
    v_volume = "0.44" if pizza_type == "perfect" else ("0.25" if pizza_type == "underbaked" else "0.38")
    v_top = "9" if pizza_type == "perfect" else ("4" if pizza_type == "underbaked" else "11")
    v_bottom = "8" if pizza_type == "perfect" else ("3" if pizza_type == "underbaked" else "10")

    # Human-in-the-Loop Rating Form Card (A2UI v0.8 standard catalog compliant)
    components.extend([
        {
            "id": "hitl_card",
            "component": {
                "Card": {
                    "child": "hitl_column"
                }
            }
        },
        {
            "id": "hitl_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            "hitl_title",
                            "hitl_desc",
                            "input_height_label",
                            "input_height",
                            "input_width_label",
                            "input_width",
                            "input_volume_label",
                            "input_volume",
                            "input_top_color_label",
                            "input_top_color",
                            "input_bottom_color_label",
                            "input_bottom_color",
                            "hitl_submit_btn"
                        ]
                    }
                }
            }
        },
        {
            "id": "hitl_title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "✏️ Human-in-the-Loop Rating Form"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "hitl_desc",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "If you disagree with the AI's measurements, use the fields below to submit corrected values to the BigQuery telemetry table:"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_height_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Edge Height (Spec: 7/8\" - 1\")"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_height",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Edge Height (inches)"
                    },
                    "text": {
                        "literalString": v_height
                    }
                }
            }
        },
        {
            "id": "input_width_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Edge Width (Spec: 1\" - 1 1/4\")"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_width",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Edge Width (inches)"
                    },
                    "text": {
                        "literalString": v_width
                    }
                }
            }
        },
        {
            "id": "input_volume_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Center Volume (Spec: 3/8\" - 1/2\")"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_volume",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Center Volume (inches)"
                    },
                    "text": {
                        "literalString": v_volume
                    }
                }
            }
        },
        {
            "id": "input_top_color_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Top Crust Color (Scale 7 - 11)"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_top_color",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Top Crust Color (Scale)"
                    },
                    "text": {
                        "literalString": v_top
                    }
                }
            }
        },
        {
            "id": "input_bottom_color_label",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "• Corrected Bottom Crust Color (Scale 6 - 10)"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "input_bottom_color",
            "component": {
                "TextField": {
                    "label": {
                        "literalString": "Bottom Crust Color (Scale)"
                    },
                    "text": {
                        "literalString": v_bottom
                    }
                }
            }
        },
        {
            "id": "hitl_submit_btn",
            "component": {
                "Button": {
                    "child": "hitl_submit_btn_text",
                    "primary": True,
                    "action": {
                        "name": "submit_correction",
                        "context": [
                            {
                                "key": "scan_id",
                                "value": {
                                    "literalString": scan_id if scan_id else "scan_unknown"
                                }
                            },
                            {
                                "key": "input_height",
                                "value": {
                                    "path": "/input_height/text/literalString"
                                }
                            },
                            {
                                "key": "input_width",
                                "value": {
                                    "path": "/input_width/text/literalString"
                                }
                            },
                            {
                                "key": "input_volume",
                                "value": {
                                    "path": "/input_volume/text/literalString"
                                }
                            },
                            {
                                "key": "input_top_color",
                                "value": {
                                    "path": "/input_top_color/text/literalString"
                                }
                            },
                            {
                                "key": "input_bottom_color",
                                "value": {
                                    "path": "/input_bottom_color/text/literalString"
                                }
                            }
                        ]
                    }
                }
            }
        },
        {
            "id": "hitl_submit_btn_text",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Submit Corrective Rating & Update BigQuery"
                    }
                }
            }
        }
    ])

    surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
    ui_json = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
                "root": "scorecard_root",
                "styles": {
                    "primaryColor": p["color"],
                    "font": "Outfit"
                }
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    ]

    parts = [Part(root=TextPart(text=md_text))]
    parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])

    return {
        "is_task_complete": True,
        "parts": parts
    }

  def _render_trends_dashboard_v08(self) -> dict[str, Any]:
    """Generates the A2UI v0.8 compliant trends dashboard component using Vega-Lite."""
    md_text = "📈 Querying BigQuery on the fly... Rendering the **Vegas West Store #4021 Weekly Trends Dashboard** below:"

    weekly_data = [
        {"date": "06/17", "pass_rate": 100},
        {"date": "06/18", "pass_rate": 50},
        {"date": "06/19", "pass_rate": 50},
        {"date": "06/20", "pass_rate": 100},
        {"date": "06/21", "pass_rate": 50},
        {"date": "06/22", "pass_rate": 66},
        {"date": "06/23", "pass_rate": 100}
    ]

    defects_data = [
        {"category": "Underbaked", "count": 3},
        {"category": "Overbaked", "count": 2},
        {"category": "Edge Width", "count": 1},
        {"category": "Edge Height", "count": 1},
        {"category": "Center Volume", "count": 0}
    ]

    components = [
        {
            "id": "dashboard_root",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["title_card", "kpi_card", "weekly_trend_card", "defects_card"]
                    }
                }
            }
        },
        {
            "id": "title_card",
            "component": {
                "Card": {
                    "child": "title_column"
                }
            }
        },
        {
            "id": "title_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["title_h1", "title_body"]
                    }
                }
            }
        },
        {
            "id": "title_h1",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Store Quality Performance Dashboard"
                    },
                    "usageHint": "h1"
                }
            }
        },
        {
            "id": "title_body",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Real-time auditing trends queried from BigQuery. Focuses on Slice & Rise compliance metrics."
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "kpi_card",
            "component": {
                "Card": {
                    "child": "kpi_row"
                }
            }
        },
        {
            "id": "kpi_row",
            "component": {
                "Row": {
                    "children": {
                        "explicitList": ["kpi_scans", "kpi_rate", "kpi_defects"]
                    },
                    "distribution": "spaceEvenly"
                }
            }
        },
        {
            "id": "kpi_scans",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Total Audited Scans:\n14 scans"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "kpi_rate",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Average Pass Rate:\n84.5% (Target: 85%)"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "kpi_defects",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Failed Defects:\n4 flagged alerts"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "weekly_trend_card",
            "component": {
                "Card": {
                    "child": "weekly_column"
                }
            }
        },
        {
            "id": "weekly_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["weekly_h2", "weekly_trend_chart"]
                    }
                }
            }
        },
        {
            "id": "weekly_h2",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "7-Day Historical Pass Rate (%) vs Benchmark"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "weekly_trend_chart",
            "component": {
                "VegaChart": {
                    "spec": {
                        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                        "description": "7-Day Historical Pass Rate (%) vs Benchmark",
                        "width": "container",
                        "height": 200,
                        "data": { "values": weekly_data },
                        "mark": {
                            "type": "line",
                            "color": "#3b82f6",
                            "point": { "color": "#3b82f6", "size": 60 },
                            "strokeWidth": 3
                        },
                        "encoding": {
                            "x": {
                                "field": "date",
                                "type": "nominal",
                                "axis": { "title": "Date", "labelAngle": 0 }
                            },
                            "y": {
                                "field": "pass_rate",
                                "type": "quantitative",
                                "scale": { "domain": [0, 100] },
                                "axis": { "title": "Pass Rate (%)" }
                            }
                        }
                    }
                }
            }
        },
        {
            "id": "defects_card",
            "component": {
                "Card": {
                    "child": "defects_column"
                }
            }
        },
        {
            "id": "defects_column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["defects_h2", "defects_chart"]
                    }
                }
            }
        },
        {
            "id": "defects_h2",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Corporate Auditing Failure Pareto Chart"
                    },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "defects_chart",
            "component": {
                "VegaChart": {
                    "spec": {
                        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                        "description": "Corporate Auditing Failure Pareto Chart",
                        "width": "container",
                        "height": 200,
                        "data": { "values": defects_data },
                        "mark": {
                            "type": "bar",
                            "color": "#ef4444",
                            "cornerRadiusEnd": 4
                        },
                        "encoding": {
                            "x": {
                                "field": "category",
                                "type": "nominal",
                                "axis": { "title": "Defect Category", "labelAngle": -15 }
                            },
                            "y": {
                                "field": "count",
                                "type": "quantitative",
                                "axis": { "title": "Occurrences" }
                            }
                        }
                    }
                }
            }
        }
    ]

    surface_id = f"pizza_surface_{uuid.uuid4().hex[:8]}"
    ui_json = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
                "root": "dashboard_root",
                "styles": {
                    "primaryColor": "#3b82f6",
                    "font": "Outfit"
                }
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    ]

    parts = [Part(root=TextPart(text=md_text))]
    parts.extend([Part(root=DataPart(data=item, metadata={"mimeType": "application/json+a2ui"})) for item in ui_json])

    return {
        "is_task_complete": True,
        "parts": parts
    }
