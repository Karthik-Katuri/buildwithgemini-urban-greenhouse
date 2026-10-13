# Copyright 2026 Google LLC
# Video generation tool for Urban Greenhouse using gemini-omni-flash-preview

import base64
import re
import uuid
from typing import Any
from google import genai
from google.genai import types as genai_types
from google.cloud import storage
from google.adk.tools import ToolContext

BUCKET_NAME = "urban-greenhouse-qwiklabs-gcp-04-93b5deb0ee1a"
PROJECT_ID = "qwiklabs-gcp-04-93b5deb0ee1a"


async def generate_plant_video(plant_name_or_prompt: str, tool_context: ToolContext) -> dict[str, Any]:
    """Generates a short video for a plant or indoor greenhouse setting using gemini-omni-flash-preview,
    saves it as an artifact in the playground, and uploads it to public Cloud Storage.

    Args:
        plant_name_or_prompt: Name of the plant or visual scene description (e.g., 'Monstera Deliciosa leaf timelapse', 'Fiddle Leaf Fig swaying gently in indoor breeze').
        tool_context: ADK ToolContext used to save session artifacts in Playground.

    Returns:
        A dictionary with the public video URL, artifact filename, and status.
    """
    try:
        # Step 1: Generate video using gemini-omni-flash-preview in global region via Interactions API
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        prompt = (
            f"A realistic, high-quality botanical video of {plant_name_or_prompt}. "
            "Smooth camera movement, natural light, healthy vibrant indoor foliage."
        )

        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt
        )

        video_bytes: bytes | None = None
        mime_type = "video/mp4"

        if interaction and interaction.output_video:
            if interaction.output_video.data:
                video_bytes = base64.b64decode(interaction.output_video.data)
            elif interaction.output_video.uri:
                # If delivered via URI, download the content bytes
                video_bytes = client.files.download(file=interaction.output_video.uri)
            if interaction.output_video.mime_type:
                mime_type = interaction.output_video.mime_type

        if not video_bytes:
            return {"error": "No video data was returned by gemini-omni-flash-preview."}

        # Safe filename slug
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", plant_name_or_prompt.strip().lower())[:30]
        unique_suffix = uuid.uuid4().hex[:8]
        filename = f"{slug}_{unique_suffix}.mp4"

        # Step 2: (1) Save artifact for ADK Playground Artifacts panel
        artifact_part = genai_types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        try:
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as artifact_err:
            print(f"Note: artifact saving skipped ({artifact_err})")

        # Step 3: (2) Upload to public Cloud Storage without writing local files
        gcs_client = storage.Client(project=PROJECT_ID)
        bucket = gcs_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"videos/{filename}")
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/videos/{filename}"

        return {
            "status": "success",
            "plant": plant_name_or_prompt,
            "filename": filename,
            "public_url": public_url,
            "message": f"Video generated successfully. Available in artifacts and at {public_url}"
        }
    except Exception as e:
        return {"error": f"Failed to generate and upload video: {str(e)}"}
