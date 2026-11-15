#!/usr/bin/env bash
# Depth map for a still image with Depth Anything V2 Small (local, free).
# Usage: depth.sh <image> <out_depth.png>
# Output: grayscale PNG at the image's size, white = near.
# Cache: ${PARALLAX_CACHE:-$HOME/.cache/parallax-2-5d} (model ~99 MB, onnxruntime-node).
set -euo pipefail
IMG="$1"; OUT="$2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C="${PARALLAX_CACHE:-$HOME/.cache/parallax-2-5d}"; mkdir -p "$C"
MODEL="$C/depth-anything-v2-small.onnx"
if [ ! -s "$MODEL" ]; then
  echo "downloading Depth Anything V2 Small (~99 MB) once..." >&2
  curl -fsSL -o "$MODEL.part" \
    https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx
  mv "$MODEL.part" "$MODEL"
fi
# onnxruntime-node: reuse HyperFrames' copy, else install once into the cache.
ORT="$(ls -d "$HOME"/.cache/hyperframes/optional/onnxruntime-node@*/node_modules/onnxruntime-node 2>/dev/null | tail -1 || true)"
if [ -z "$ORT" ]; then
  ORT="$C/node/node_modules/onnxruntime-node"
  if [ ! -d "$ORT" ]; then
    echo "installing onnxruntime-node once..." >&2
    npm install --silent --no-audit --no-fund --prefix "$C/node" onnxruntime-node@1.21.1 >&2
  fi
fi
python3 -c "import numpy, PIL" 2>/dev/null || { echo "needs python3 with numpy and Pillow (pip install numpy pillow)" >&2; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
read -r W H < <(python3 -I "$HERE/depth_pre.py" "$IMG" "$TMP/in.f32")
node "$HERE/depth_run.cjs" "$ORT" "$MODEL" "$TMP/in.f32" "$W" "$H" "$TMP/out.f32" >/dev/null
python3 -I "$HERE/depth_post.py" "$TMP/out.f32" "$W" "$H" "$IMG" "$OUT"
echo "$OUT"
