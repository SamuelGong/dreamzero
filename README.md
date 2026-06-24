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

Suppose that they are located at `$DROID_DIR` and  `$WAN_DIR`, respectively.

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

The generated videos (consisting of predicted frames) will be at `$DROID_DIR/../real_world_eval_gen_{date}_{index}/{model_name}/`.

## Step 4: Simulation with Sim-Evals

> Isaac Sim used by `sim-evals` needs to run with GPUs that have RT cores. Here I use Ubuntu 20.04 with L40 GPus to serve as an example.

Preparing the simulation environment. First, manually install NVIDIA's Isaac Sim:

```bash
# Reference: https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/binaries_installation.html
cd $HOME  # or anywhere else that suits

# Isaac Sim (here 4.2.0 was used)
wget --no-check-certificate https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone%404.2.0-rc.18%2Brelease.16044.3b2ed111.gl.linux-x86_64.release.zip
unzip isaac-sim-standalone%404.2.0-rc.18%2Brelease.16044.3b2ed111.gl.linux-x86_64.release.zip -d isaacsim

# For testing
export ISAACSIM_PATH="${HOME}/isaacsim"
export ISAACSIM_PYTHON_EXE="${ISAACSIM_PATH}/python.sh"

cd dreamzero
chmod +x ./test_isaac_sim.sh
./test_isaac_sim.sh  # as an alternative for directly running "$ISAACSIM_PATH/isaac-sim.sh"
# Attention: could not be changed to "source ./test_isaac_sim.sh"
# On success, one should see something like:
# [94.378s] app ready
# [94.651s] Isaac Sim App is loaded

./test_isaac_sim_python.sh
# One should see similar output
```

and also Isaac Lab:

```bash
# Reference: https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/binaries_installation.html
cd $HOME  # or anywhere else that suits

git clone https://github.com/isaac-sim/IsaacLab.git --branch main
cd IsaacLab
ln -s ${ISAACSIM_PATH} _isaac_sim

./isaaclab.sh --conda dreamzero
no_proxy="$no_proxy,.huawei.com,localhost,127.0.0.1" NO_PROXY="$NO_PROXY,.huawei.com,localhost,127.0.0.1" pip install --no-build-isolation torch==2.7.0 --trusted-host download-r2.pytorch.org
/isaaclab.sh -i

```




```bash
git -c http.sslVerify=false clone --recurse-submodules https://github.com/arhanjain/sim-evals.git
cd sim-evals
```

```bash
conda activate dreamero
no_proxy="$no_proxy,.huawei.com,localhost,127.0.0.1" NO_PROXY="$NO_PROXY,.huawei.com,localhost,127.0.0.1" pip install uv --trusted-host pypi.org --trusted-host files.pythonhosted.org

```

