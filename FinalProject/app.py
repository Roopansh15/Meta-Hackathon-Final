import os

try:
    import huggingface_hub

    if not hasattr(huggingface_hub, "HfFolder"):
        class HfFolder:
            @staticmethod
            def get_token():
                return os.environ.get("HF_TOKEN")

            @staticmethod
            def save_token(token):
                os.environ["HF_TOKEN"] = token

            @staticmethod
            def delete_token():
                os.environ.pop("HF_TOKEN", None)

        huggingface_hub.HfFolder = HfFolder
except Exception:
    pass

import gradio as gr
from src.inboxworld.types import InboxEmail
from src.inboxworld.llm_inference import LLMEmailPolicy

BUILD_VERSION = "hf-llm-debug-v3-2026-07-03"

# Initialize the Production LLM Pipeline (Falls back to local multi-agent heuristics if no API key is present)
policy = LLMEmailPolicy()

def process_email_demo(sender, subject, body, sender_importance, is_urgent):
    """Takes input from the UI and passes it through your Multi-Agent system."""
    
    # Pack the input into your InboxEmail type
    test_email = InboxEmail(
        email_id="demo-1",
        sender=sender,
        sender_importance=sender_importance.lower(),
        subject=subject,
        body=body,
        priority="unknown",
        urgency=is_urgent,
        visible_urgency=is_urgent,
        deadline_step=1 if is_urgent else None,
        hidden_intent="unknown",
        expected_action="unknown",
        expected_tone="unknown",
        thread_id="thread-none",
        tags=[]
    )
    
    # Run your multi-agent architecture!
    action = policy.act({"emails": [test_email]})
    
    # Format the output gracefully for the UI
    priority_result = f"{action.predicted_priority.upper()} (Urgent: {action.predicted_urgency})"
    action_result = action.action_type.replace("_", " ").title()
    tone = action.reply_tone.title() if action.reply_tone else "None"
    
    # Create the rationale to show the evaluation committee
    metadata_lines = [
        f"- Inference: {action.metadata.get('llm_inference', 'local')}",
        f"- Model: {action.metadata.get('model', 'local-policy')}",
    ]
    if "provider" in action.metadata:
        metadata_lines.append(f"- Provider: {action.metadata.get('provider')}")
    if "hf_token_present" in action.metadata:
        metadata_lines.append(f"- HF token present: {action.metadata.get('hf_token_present')}")
    if "llm_error" in action.metadata:
        metadata_lines.append(f"- LLM error: {action.metadata.get('llm_error')}")
    metadata_lines.extend([
        f"- Target: {action.escalate_target}",
        f"- Delay: {action.delay_steps} steps",
    ])
    metadata = "\n".join(metadata_lines)
    
    return priority_result, action_result, tone, action.response_text, metadata


# --- BUILD THE WEB UI ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# InboxWorld: Multi-Agent Policy Demo")
    gr.Markdown(f"**Hosted build:** `{BUILD_VERSION}`")
    gr.Markdown("This interactive UI visualizes the decision-making logic of the training-ready architecture. Type an incoming email below and see how the Classifier, Priority, Responder, and Supervisor Agents handle it.")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Incoming Email")
            sender_input = gr.Textbox(label="Sender Name", value="John Doe")
            importance_input = gr.Dropdown(choices=["boss", "client", "friend", "normal"], value="boss", label="Sender Importance")
            urgent_input = gr.Checkbox(label="Has Visible Urgency?", value=False)
            subject_input = gr.Textbox(label="Email Subject", value="Project Milestone")
            body_input = gr.Textbox(label="Email Body", lines=5, value="Hey team, when will we hit the renewal milestone? We need this by today.")
            
            submit_btn = gr.Button("Send to Agents", variant="primary")
            
        with gr.Column():
            gr.Markdown("### Multi-Agent Output")
            priority_output = gr.Textbox(label="Assessed Priority")
            action_output = gr.Textbox(label="Agent Action")
            tone_output = gr.Textbox(label="Agent Tone")
            response_output = gr.Textbox(label="Prepared Response", lines=2)
            meta_output = gr.Textbox(label="Additional Metadata", lines=2)
            
    submit_btn.click(
        fn=process_email_demo,
        inputs=[sender_input, subject_input, body_input, importance_input, urgent_input],
        outputs=[priority_output, action_output, tone_output, response_output, meta_output]
    )

if __name__ == "__main__":
    demo.launch()
