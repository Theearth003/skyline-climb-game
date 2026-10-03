# Genie-1 — Saved Architecture & Training Cell

Genie-1 architecture: ~678.36M parameters
Hidden size: 1,024
Layers: 18
Workspace: 32
Memory slots: 128
Experts: 4, with all 4 active
Vocabulary: 32,768
Context length: 2,048
Forward test: (1,128) → (1,128,32768)
Dataset: MemoryMappedTokenDataset
Dataset size: 1,464,843 sequences
Dataset interface included get_batch()

Training was split into:
- Genie-1_Training_1A — dataset discovery, memory-mapped uint16 tokens, optimizer, FP16, gradient checkpointing, checkpoint/resume, memory testing
- Genie-1_Training_1B — actual training loop

Micro-batch: 1
Gradient accumulation: 16
Tokens per optimizer step: 32,768
Target training data: 3.3B tokens
Estimated steps: ~100,708
Checkpoint interval: every 500 steps

Checkpointing was based on global optimizer steps so training could pause/resume correctly.

Latest remembered checkpoint: ~7.58 GB
Checkpoint path:
/kaggle/working/genie1_checkpoints/latest_checkpoint.pt
