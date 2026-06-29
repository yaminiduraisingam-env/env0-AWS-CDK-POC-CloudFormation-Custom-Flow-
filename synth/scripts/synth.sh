#!/usr/bin/env bash
#
# Run by the env0 Custom Flow at setupVariables.after (deploy and destroy).
# Installs the Python CDK dependencies and synthesizes the CDK app into a plain
# CloudFormation template that env0's CloudFormation IaC type then deploys.
#
set -euo pipefail

# Must match the "CloudFormation file" path configured on the env0 template.
export CDK_OUTDIR="synth"

echo "==> Installing Python CDK dependencies"
# env0 runners ship Python 3 + pip. --break-system-packages keeps pip happy on
# PEP 668 (externally managed) base images and is harmless when not needed.
python3 -m pip install --quiet --break-system-packages -r requirements.txt

echo "==> Synthesizing CDK app into ${CDK_OUTDIR}/"
# Running the app directly calls app.synth(), which is equivalent to `cdk synth`
# for this asset-free app and needs no Node.js or cdk CLI on the runner.
#
# If you prefer the canonical CLI and Node is available on the runner, you can
# swap the line below for:
#   npx --yes aws-cdk@2 synth --output "${CDK_OUTDIR}"
python3 app.py

TEMPLATE="${CDK_OUTDIR}/WesternUnionCdkPoc.template.json"
if [ ! -f "${TEMPLATE}" ]; then
  echo "Synth did not produce ${TEMPLATE}" 1>&2
  exit 1
fi

echo "==> Synth complete: ${TEMPLATE}"
