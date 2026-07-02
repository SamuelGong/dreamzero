# Personal Guidance for Running Toy Example

If you are *not* using the company's internal network, simply follow the instructions on original [README](./README-original.md).

Otherwise, follow me:

## 1. Dreamzero Policy Server

> Here I use Ubuntu 22.04 with 3 H800 GPUs and NIVIDIA 580.82.07 Driver to serve as an example.

### 1.1 Installation

```bash
git clone git@github.com:SamuelGong/dreamzero.git
cd dreamzero

conda create -n dreamzero python=3.11
conda activate dreamzero

conda install -c conda-forge pyqt
pip install tensorrt-cu13-libs
pip install -e .

MAX_JOBS=32 pip install --no-build-isolation flash-attn  # 32 here can be something larger
# If failed because "invalid cross-device link" (probably because your temp folder and pip cache are using different disks)
# Try this instead (The version is extracted from the error prompt):
# wget -O flash_attn-2.8.3.post1+cu12torch2.8cxx11abiTRUE-cp311-cp311-linux_x86_64.whl \
# "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3.post1/flash_attn-2.8.3.post1+cu12torch2.8cxx11abiTRUE-cp311-cp311-linux_x86_64.whl"
# 
```

### 1.2 Downloading Models A Priori

Use the script `download_model.py` to download the following required models `GEAR-Dreams/DreamZero-DROID` and `Wan-AI/Wan2.1-I2V-14B-480P`.

```bash
# if not with the flag --use-mirror, one needs to use VPN or otherwise things can get extremely slow
python download_model.py GEAR-Dreams/DreamZero-DROID  --use-mirror
python download_model.py Wan-AI/Wan2.1-I2V-14B-480P --use-mirror
```

And remember their paths.

Suppose that they are located at `$DROID_DIR` and  `$WAN_DIR`, respectively, something like:

```
/root/autodl-tmp/jiangzhifeng/.cache/huggingface/hub/models--GEAR-Dreams--DreamZero-DROID/snapshots/96ad344138c66e82536422432ad742f015784942/
```

, and

```
/root/autodl-tmp/jiangzhifeng/.cache/huggingface/hub/models--Wan-AI--Wan2.1-I2V-14B-480P/snapshots/6b73f84e66371cdfe870c72acd6826e1d61cf279/
```

## Step 3: Toy Server-Client example

First, go to the directory of the downloaded `GEAR-Dreams/DreamZero-DROID`.
where we will do some configurations as follows.

1. For `config.json`:
   1. `action_head_cfg/config/diffusion_model_cfg/diffusion_model_pretrained_path`: change it to the path to `$WAN_DIR`.
   2. `action_head_cfg/config/image_encoder_cfg/image_encoder_pretrained_path`: change it to the path to `$WAN_DIR/models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth`.
   3. `action_head_cfg/config/text_encoder_cfg/text_encoder_pretrained_path`: change it to the path to `$WAN_DIR/models_t5_umt5-xxl-enc-bf16.pth`.
   4. `action_head_cfg/config/vae_cfg/vae_pretrained_path`: change it to the path to `$WAN_DIR/"Wan2.1_VAE.pth`.
2. For `experiment_cfg/conf.yaml`:
   1. `oxe_droid/transforms/tokenizer_path`: change it to the path to `$WAN_DIR/google/umt5-xxl`.

Then return to the project root, and open two separate terminal session to simulate the server and the client:

**Server**

```bash
CUDA_VISIBLE_DEVICES=0 python -m torch.distributed.run --standalone --nproc_per_node=1 socket_test_optimized_AR.py --port 6006 --enable-dit-cache --model-path <path to the downloaded GEAR-Dreams/DreamZero-DROID>
```

One can use more cores like:

```bash
CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.run --standalone --nproc_per_node=2 socket_test_optimized_AR.py --port 6006 --enable-dit-cache --model-path <path to the downloaded GEAR-Dreams/DreamZero-DROID>
```

**Client**

```bash
python test_client_AR.py --port 6006
# the server side should finally print something like:
# INFO:__main__:Saved video on reset to: /root/autodl-tmp/jiangzhifeng/.cache/huggingface/hub/models--GEAR-Dreams--DreamZero-DROID/snapshots/96ad344138c66e82536422432ad742f015784942/real_world_eval_gen_20260702_0/000000_07_02_09_42_01_n17.mp4
```

As shown, the generated videos (consisting of predicted frames) will be at `$DROID_DIR/real_world_eval_gen_{date}_{index}/{model_name}/`.

## 2. Simulation with Sim-Evals

[Reference](https://github.com/dreamzero0/dreamzero/blob/main/README.md#testing-out-dreamzero-in-simulation-with-api)

> Isaac Sim used by `sim-evals` needs to run with GPUs that have RT cores. Here I use Ubuntu 22.04 with RTX PRO 6000 GPUs and NIVIDIA 580.95.05 Driver to serve as an example.

First we need to install system-related packages or drivers.

```bash
apt-get update
apt-get install -y vulkan-tools
apt-get install -y \
  libxt6 \
  libglu1-mesa \
  libgl1 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxext6 \
  libxrender1 \
  libxi6 \
  libxrandr2 \
  libxinerama1 \
  libxcursor1 \
  libxkbcommon-x11-0 \
  libsm6 \
  libice6 \
  vulkan-tools

cat > /usr/share/vulkan/icd.d/nvidia_icd.json <<'EOF'
{
    "file_format_version": "1.0.0",
    "ICD": {
        "library_path": "libEGL_nvidia.so.0",
        "api_version": "1.3.0"
    }
}
EOF

echo 'export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json' >> ~/.bashrc
source ~/.bashrc
vulkaninfo --summary  # Should see some line like "deviceName = NVIDIA RTX PRO 6000 Blackwell Server Edition"
```

Then simulation software things:

```bash
apt install ffmpeg

git clone git@github.com:SamuelGong/dreamzero.git
cd dreamzero

git -c http.sslVerify=false clone --recurse-submodules https://github.com/arhanjain/sim-evals.git
# i.e., now you should have a folder named sim-evals under the path to dreamzero 
cd sim-evals
vim pyproject.toml
# add this line:
# build-constraint-dependencies = ["setuptools<82"]
# to under [tool.uv]
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
source $HOME/.local/bin/env
# 'uv sync' needs an environment that has Python
# if there is not, that we need to create one for temporary use as follows
# conda create -n temp Python=3.11 -y
# conda activate temp
uv sync
conda deactivate
# may repeat 'conda deactivate' serveral times
# until you are no longer in any conda environment, including base

source .venv/bin/activate
pip install torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu129
# Download assets (may need to export HF_TOKEN=<YOUR_HUGGINGFACE_TOKEN> first)
uvx hf download owhan/DROID-sim-environments --repo-type dataset --local-dir assets

cd ..  # go back the the root directory of dreamzero
pip install -e .
python eval_utils/run_sim_eval.py \
  --host [IP to the policy server] \
  --port 6006
```

**Rollout Videos**

On success, one should see the resulting videos at folders like `runs/2026-07-02/10-55-03`.
One of the videos looks like [example-rollout.mp4](./example-rollout.mp4).

Note that the videos are not predicted ones.
They are rollout videos, i.e., actual observations in the Issac Sim based on the policy generated by the server.

As for generated video predictions, they are on the policy server with paths as mentioned above.
One of the videos looks like [example-predicted.mp4](./example-predicted.mp4).