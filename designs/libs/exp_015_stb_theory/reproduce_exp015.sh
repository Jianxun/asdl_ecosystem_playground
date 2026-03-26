#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

RUN_ID="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
RUN_DIR="${REPO_ROOT}/runs/exp_015_stb_theory/${RUN_ID}"

GM="${GM:-1e-3}"
GO="${GO:-2e-4}"
GI="${GI:-1e-4}"
COUT="${COUT:-1e-12}"
CIN="${CIN:-1e-12}"

RO="${RO:-5000}"
RI="${RI:-10000}"

mkdir -p "${RUN_DIR}"

echo "[exp015] run_id=${RUN_ID}"
echo "[exp015] run_dir=${RUN_DIR}"
echo "[exp015] params: GM=${GM} GO=${GO} GI=${GI} COUT=${COUT} CIN=${CIN}"

asdlc netlist "${REPO_ROOT}/libs/exp_015_stb_theory/tb_dc_middlebrook_series.asdl" --backend sim.xyce -o "${RUN_DIR}/tb_dc_middlebrook_series.spice"
asdlc netlist "${REPO_ROOT}/libs/exp_015_stb_theory/tb_dc_middlebrook_shunt.asdl" --backend sim.xyce -o "${RUN_DIR}/tb_dc_middlebrook_shunt.spice"
asdlc netlist "${REPO_ROOT}/libs/exp_015_stb_theory/tb_ac_middlebrook_series.asdl" --backend sim.xyce -o "${RUN_DIR}/tb_ac_middlebrook_series.spice"
asdlc netlist "${REPO_ROOT}/libs/exp_015_stb_theory/tb_ac_middlebrook_shunt.asdl" --backend sim.xyce -o "${RUN_DIR}/tb_ac_middlebrook_shunt.spice"

xyce "${RUN_DIR}/tb_dc_middlebrook_series.spice"
xyce "${RUN_DIR}/tb_dc_middlebrook_shunt.spice"
xyce "${RUN_DIR}/tb_ac_middlebrook_series.spice"
xyce "${RUN_DIR}/tb_ac_middlebrook_shunt.spice"

"${REPO_ROOT}/venv/bin/python" "${REPO_ROOT}/analysis/tools/xyce/raw_to_h5.py" "${RUN_DIR}/tb_dc_middlebrook_series.spice.raw"
"${REPO_ROOT}/venv/bin/python" "${REPO_ROOT}/analysis/tools/xyce/raw_to_h5.py" "${RUN_DIR}/tb_dc_middlebrook_shunt.spice.raw"
"${REPO_ROOT}/venv/bin/python" "${REPO_ROOT}/analysis/tools/xyce/raw_to_h5.py" "${RUN_DIR}/tb_ac_middlebrook_series.spice.raw"
"${REPO_ROOT}/venv/bin/python" "${REPO_ROOT}/analysis/tools/xyce/raw_to_h5.py" "${RUN_DIR}/tb_ac_middlebrook_shunt.spice.raw"

"${REPO_ROOT}/venv/bin/python" "${REPO_ROOT}/analysis/tools/xyce/analyze_middlebrook_dc_two_pass.py" \
  "${RUN_DIR}" --gm "${GM}" --go "${GO}" --gi "${GI}"

"${REPO_ROOT}/venv/bin/python" "${REPO_ROOT}/analysis/tools/xyce/analyze_middlebrook_ac_two_pass.py" \
  "${RUN_DIR}" --gm "${GM}" --go "${GO}" --gi "${GI}" --cout "${COUT}" --cin "${CIN}"

"${REPO_ROOT}/venv/bin/python" "${SCRIPT_DIR}/postprocess_exp015.py" \
  "${RUN_DIR}" --gm "${GM}" --go "${GO}" --gi "${GI}" --cout "${COUT}" --cin "${CIN}" --ro "${RO}" --ri "${RI}"

echo "[exp015] done"
echo "[exp015] artifacts: ${RUN_DIR}"
