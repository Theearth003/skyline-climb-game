# Genie Model

This repository is now the home of the **Genie** model project.

## Genie-1 recovered specification

- Approx. parameters: **678.36M**
- Hidden size: **1024**
- Layers: **18**
- Workspace: **32**
- Memory slots: **128**
- Experts: **4** (all 4 active)
- Vocabulary: **32,768**
- Context length: **2,048**
- Forward test: input `(1, 128)` → output `(1, 128, 32768)`

## Training

- Dataset interface: `MemoryMappedTokenDataset`
- Dataset size: **1,464,843 sequences**
- Tokenizer: same **32K tokenizer** used by the SLM work
- Target training volume: **3.3B tokens**
- Micro-batch size: **1**
- Gradient accumulation: **16**
- Tokens per optimizer step: **32,768**
- Estimated optimizer steps: **~100,708**
- Checkpoint interval: **every 500 optimizer steps**
- Checkpoint path used in training: `/kaggle/working/genie1_checkpoints/latest_checkpoint.pt`
- Latest remembered checkpoint size: **7.58 GB**

## Training notebook structure

The remembered workflow was split into:

### Genie-1_Training_1A
- Dataset discovery
- Memory-mapped uint16 token loading
- Optimizer setup
- FP16
- Gradient checkpointing
- Checkpoint/resume support
- Memory testing

### Genie-1_Training_1B
- Main training loop
- Global optimizer-step checkpointing
- Pause/resume training

## Important note

This README records the Genie-1 specification and training details currently recovered from the project history. It does **not** claim to contain the exact original notebook cell-by-cell source code. The original `.ipynb` is required to reconstruct every cell exactly without inventing missing code.

Repository renamed conceptually from **Skyline Climb Game** to **Genie Model**.
