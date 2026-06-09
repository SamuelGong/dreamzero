# Personal Guidance for Running Toy Example

If you are *not* using the company's internal network, simply follow the instructions on original [README](./README-original.md).

Otherwise, follow me:

## Step 1: Installation

```bash
conda create -n dreamzero python=3.11
conda activate dreamzero

conda install -c conda-forge pyqt
pip install --extra-index-url https://pypi.nvidia.com/ tensorrt-cu13-libs --trusted-host pypi.nvidia.com
no_proxy="$no_proxy,.huawei.com,localhost,127.0.0.1" NO_PROXY="$NO_PROXY,.huawei.com,localhost,127.0.0.1" pip install --no-build-isolation -e . --extra-index-url https://download.pytorch.org/whl/cu129 --trusted-host download-r2.pytorch.org --trusted-host pypi.nvidia.com

MAX_JOBS=8 no_proxy="$no_proxy,.huawei.com,localhost,127.0.0.1" NO_PROXY="$NO_PROXY,.huawei.com,localhost,127.0.0.1" pip install --no-build-isolation flash-attn  # 8 here can be something larger
```

## Step 2: Downloading Models A Priori

Use the script `download_model.sh` to download the following required models 
(by modifying the `REPO_ID` and `SAVE_DIR` respectively) from huggingface:

- GEAR-Dreams/DreamZero-DROID
- Wan-AI/Wan2.1-I2V-14B-480P

And remember their paths.

Suppose that they are located at `$DROID_PATH` and  `$WAN_DIR`, respectively.

## Step 3: Toy Server-Client example

First, go to the directory of the downloaded GEAR-Dreams/DreamZero-DROID.
where we will do some configurations as follows.

1. For `config.json`:
   1. `action_head_cfg/config/diffusion_model_cfg/diffusion_model_pretrained_path`: change it to the path to `$WAN_DIR`.
   2. `action_head_cfg/config/image_encoder_cfg/image_encoder_pretrained_path`: change it to the path to `$WAN_DIR/models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth`.
   3. `action_head_cfg/config/text_encoder_cfg/text_encoder_pretrained_path`: change it to the path to `$WAN_DIR/models_t5_umt5-xxl-enc-bf16.pth`.
   4. `action_head_cfg/config/vae_cfg/vae_pretrained_path`: change it to the path to `$WAN_DIR/Wan2.1_VAE.pth`.
2. For `experiment_cfg/conf.yaml`:
   1. `oxe_droid/transforms/tokenizer_path`: change it to the path to `$WAN_DIR/google/umt5-xxl`.

Then return to the project root, and open two separate terminal session to simulate the server and the client:

**Server**

```bash
CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.run --standalone --nproc_per_node=2 socket_test_optimized_AR.py --port 5000 --enable-dit-cache --model-path <path to the downloaded GEAR-Dreams/DreamZero-DROID>
```

**Client**

```bash
python test_client_AR.py --port 5000
```