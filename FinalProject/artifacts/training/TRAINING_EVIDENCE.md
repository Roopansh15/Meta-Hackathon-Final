# InboxWorld Colab Training Evidence

This folder contains proof that the InboxWorld training pipeline was run in Google Colab on a T4 runtime.

## Files

- `transition_buffer.json`: prompt/action/reward transitions generated from the InboxWorld environment.
- `loss_curve_colab.png`: loss curve from the minimal Hugging Face TRL training run.
- `model_output_sample_raw.json`: raw smoke-test output from the tiny fine-tuned model. This is kept for transparency, but the final live demo uses Hugging Face hosted LLM inference plus the local multi-agent fallback.

## Judge-Facing Claim

InboxWorld provides a working environment, reward function, transition collection pipeline, and minimal HF TRL fine-tuning script. The Colab run demonstrates that the generated transitions can be used to train a small model. The live demo uses hosted LLM inference for natural responses while the benchmark evaluates the environment and policy behavior.
