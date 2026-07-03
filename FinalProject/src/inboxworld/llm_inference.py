import os
import json
from typing import Dict, Any


EMERGENCY_KEYWORDS = [
    "heart attack",
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "stroke",
    "bleeding",
    "unconscious",
    "medical emergency",
    "emergency",
    "hospital",
    "ambulance",
    "call 911",
]

class LLMEmailPolicy:
    """
    Production Inference Pipeline using Serverless Hugging Face API.
    Provides a real LLM experience for the Gradio UI demo.
    """
    def __init__(self):
        self.token = self._get_token()
        self.last_error = ""
        try:
            from huggingface_hub import InferenceClient
            self.model = os.environ.get("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
            self.provider = os.environ.get("HF_PROVIDER") or None
            self.client = InferenceClient(self.model, provider=self.provider, token=self.token)
            self.api_available = True
        except ImportError as e:
            self.model = "local-fallback"
            self.provider = None
            self.last_error = f"ImportError: {e}"
            self.api_available = False

    def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends the state vector to the real LLM for semantic understanding.
        """
        emails = state.get("emails", [])
        if not emails or not self.api_available:
            return self._fallback(state)

        email = emails[0]
        from .types import EmailAgentAction
        
        system_prompt = (
            "You are InboxWorld, a careful corporate email triage agent. "
            "Classify the email and draft a safe response when needed. "
            "Use only facts present in the email and metadata. Do not invent status, promises, dates, names, or progress. "
            "If the email asks for information the user may need to verify, say you will check and follow up. "
            "Tone guide: use professional for workplace/client messages, friendly for casual messages, "
            "empathetic for personal distress, and urgent for medical or safety emergencies. "
            "For hospital, medical, or safety messages, acknowledge concern and advise contacting local emergency services "
            "if immediate help is needed. "
            "Do not include placeholders like [Your Name], signatures, or markdown. "
            "Keep response_text concise: 2-4 sentences. "
            "Return a pure JSON object (no markdown, no extra text) with EXACTLY these keys: "
            "priority ('high', 'medium', 'low'), action_type ('generate_reply', 'escalate_email', 'delay_email', 'ignore_email'), "
            "reply_tone ('professional', 'friendly', 'helpful', 'empathetic', 'urgent', 'neutral'), and response_text."
        )
        
        user_prompt = (
            f"Sender: {email.sender}\n"
            f"Sender Importance: {email.sender_importance}\n"
            f"Visible Urgency: {email.visible_urgency}\n"
            f"Subject: {email.subject}\n"
            f"Body: {email.body}\n"
            "Generate the JSON decision. For response_text, draft as the user or team, but stay cautious and grounded."
        )

        try:
            # Hit the public free inference endpoint
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=220,
                temperature=0.2,
                seed=42
            )
            
            completion = response.choices[0].message.content.strip()
            
            # Clean markdown JSON blocks if the LLM adds them
            if completion.startswith("```json"):
                completion = completion[7:-3]
            elif completion.startswith("```"):
                completion = completion[3:-3]
                
            data = json.loads(completion)
            
            from .types import EmailAgentAction
            from dataclasses import asdict
            return EmailAgentAction(
                email_id=email.email_id,
                action_type=data.get("action_type", "generate_reply"),
                predicted_priority=data.get("priority", "medium"),
                predicted_urgency=True if data.get("priority") == "high" else False,
                reply_tone=data.get("reply_tone", "professional"),
                response_text=self._clean_response_text(data.get("response_text", "No response generated.")),
                metadata={"llm_inference": "success", "model": self.model}
            )
            
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {str(e)}"
            print(f"[LLM Inference Failed for {self.model} - Using Fallback]: {self.last_error}")
            return self._fallback(state, self.last_error)

    def _fallback(self, state: Dict[str, Any], error: str = ""):
        from .agents import MultiAgentEmailPolicy
        fallback = MultiAgentEmailPolicy()
        action = fallback.act(state)
        action.metadata["llm_inference"] = "fallback"
        action.metadata["model"] = self.model
        action.metadata["provider"] = self.provider or "auto"
        action.metadata["hf_token_present"] = bool(self.token)
        if error or self.last_error:
            action.metadata["llm_error"] = error or self.last_error
        return action

    def _get_token(self) -> str | None:
        return (
            os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN")
            or os.environ.get("HF_ACCESS_TOKEN")
        )

    def _clean_response_text(self, text: str) -> str:
        banned_fragments = [
            "[Your Name]",
            "Best regards,",
            "Sincerely,",
            "Regards,",
        ]
        cleaned = text.strip()
        for fragment in banned_fragments:
            cleaned = cleaned.replace(fragment, "").strip()
        return cleaned
