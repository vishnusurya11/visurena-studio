#!/usr/bin/env bash
# Run the bench arms one job at a time, each only in a gap of the live episode:
# ComfyUI queue empty, GPU util < 15 %, >= 2.5 GB VRAM free.  Appends JSON lines to timings.jsonl.
#   bash run_arms.sh <nvvfx_dir> [take ...]
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VFX="$1"; shift
TAKES="${*:-T17 T03 T06}"
PY=/d/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/python_embeded/python.exe
OUT="$HERE/arms"; mkdir -p "$OUT"
LOG="$HERE/timings.jsonl"

idle() {  # Windows tools end lines in CR: keep digits only
  local q util free
  q=$(curl -s http://127.0.0.1:8188/queue | python -c "import json,sys;d=json.load(sys.stdin);print(len(d['queue_running'])+len(d['queue_pending']))" | tr -cd '0-9')
  read -r util free < <(nvidia-smi --query-gpu=utilization.gpu,memory.free --format=csv,noheader,nounits | tr -cd '0-9 \n')
  [ "$q" = "0" ] && [ "$util" -lt 15 ] && [ "$free" -ge 2500 ]
}

wait_gap() { until idle; do sleep 10; done; }

arm_a() {  # today's assemble path: lanczos 2x, x264 slow CRF 14
  local t=$1 s e
  wait_gap
  s=$(date +%s.%N)
  ffmpeg -y -v error -i "$HERE/src/$t.mp4" -vf "scale=1536:1536:flags=lanczos,format=yuv420p" \
    -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -c:a copy "$OUT/${t}_A.mp4"
  e=$(date +%s.%N)
  echo "{\"take\":\"$t\",\"arm\":\"A\",\"mode\":\"lanczos\",\"wall_s\":$(python -c "print(round($e-$s,2))" | tr -cd '0-9.'),\"gpu_s\":0}" >> "$LOG"
}

arm_vsr() {  # take arm scale MODE [PRE]
  local t=$1 arm=$2 scale=$3 mode=$4 pre=${5:-} line
  wait_gap
  line=$("$PY" -I "$HERE/tools/vsr_arm.py" "$VFX" "$HERE/src/$t.mp4" "$OUT/${t}_${arm}.mp4" "$scale" "$mode" $pre | tr -d '\r')
  echo "{\"take\":\"$t\",\"arm\":\"$arm\",${line#\{}" >> "$LOG"
  echo "$t $arm $line"
}

for t in $TAKES; do
  arm_a "$t"
  arm_vsr "$t" B "2" HIGHBITRATE_ULTRA
  arm_vsr "$t" C "2" HIGHBITRATE_ULTRA DEBLUR_ULTRA   # deblur at 1x, then B
  arm_vsr "$t" D "4" ULTRA
  arm_vsr "$t" U2 "2" ULTRA                           # the installed node's standard 2x (round 0's arm)
done
