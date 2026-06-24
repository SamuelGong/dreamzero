#!/bin/bash
unset DISPLAY
unset WAYLAND_DISPLAY
unset XAUTHORITY
unset LD_LIBRARY_PATH
unset PYTHONPATH
unset VK_LAYER_PATH

export VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json

cd "$ISAACSIM_PATH"
./isaac-sim.sh --headless --no-window
