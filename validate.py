#!/usr/bin/env python3
"""
End-to-end validation script for an ADK Agent deployed on Vertex AI Agent Engine
behind an Agent Gateway in VPC-SC.
"""

import argparse
import sys
import vertexai


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an ADK Reasoning Engine deployment end-to-end."
    )
    parser.add_argument(
        "--project",
        default="<YOUR_PROJECT_ID>",
        help="GCP project ID (default: <YOUR_PROJECT_ID>).",
    )
    parser.add_argument(
        "--region",
        default="us-central1",
        help="GCP region (default: us-central1).",
    )
    parser.add_argument(
        "--engine-id",
        required=True,
        help="Reasoning Engine ID (e.g., 9096670364183822336) or full resource name.",
    )
    parser.add_argument(
        "--prompt",
        default="Hello! Please confirm you are responding through the Agent Gateway.",
        help="Test prompt to send to the agent.",
    )
    args = parser.parse_args()

    resource_name = (
        args.engine_id
        if args.engine_id.startswith("projects/")
        else f"projects/{args.project}/locations/{args.region}/reasoningEngines/{args.engine_id}"
    )

    print(f"[*] Initializing Vertex AI Client (project={args.project}, region={args.region})...")
    client = vertexai.Client(project=args.project, location=args.region)
    engine = client.agent_engines.get(name=resource_name)
    print(f"[*] Connected to Reasoning Engine: {engine.api_resource.name}")
    print(f"[*] Sending prompt: '{args.prompt}'\n")

    received_text = []
    model_version = None

    for event in engine.stream_query(message=args.prompt, user_id="validation-user"):
        if isinstance(event, dict):
            if "error_code" in event:
                print(f"[ERROR] Runtime returned error event: {event}", file=sys.stderr)
                return 1
            model_version = event.get("model_version") or model_version
            content = event.get("content", {})
            for part in content.get("parts", []):
                if "text" in part:
                    received_text.append(part["text"])

    full_response = "".join(received_text).strip()
    if not full_response:
        print("[ERROR] No response text received from agent.", file=sys.stderr)
        return 1

    print(f"[✓] Received Model Response (model: {model_version}):")
    print("-" * 60)
    print(full_response)
    print("-" * 60)
    print("\n[✓] End-to-end query validation PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
