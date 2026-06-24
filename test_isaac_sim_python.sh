#!/usr/bin/env bash
set -euo pipefail

exec env -i \
  HOME="$HOME" \
  USER="$USER" \
  PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  ISAACSIM_PATH="$ISAACSIM_PATH" \
  ISAACSIM_PYTHON_EXE="$ISAACSIM_PYTHON_EXE" \
  VK_ICD_FILENAMES="/etc/vulkan/icd.d/nvidia_icd.json" \
  OMNI_KIT_ACCEPT_EULA=YES \
  "$ISAACSIM_PYTHON_EXE" \
  "$ISAACSIM_PATH/standalone_examples/api/omni.isaac.core/add_cubes.py" \
  --headless