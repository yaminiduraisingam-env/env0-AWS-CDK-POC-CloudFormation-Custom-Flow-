#!/usr/bin/env python3
"""env0 + AWS CDK POC for Western Union.

This app synthesizes a single, self-contained CloudFormation template that
env0's CloudFormation IaC type deploys with `aws cloudformation deploy`.

The env0 Custom Flow (see env0.yml) runs the synth step at the earliest hook
(setupVariables.after), so the template exists on disk before env0 runs its
native CloudFormation deploy/destroy. That keeps the deployment fully
env0-managed: drift detection, RBAC, change-set review, destroy, and so on.

We use CliCredentialsStackSynthesizer so the synthesized template has no
bootstrap roles, no asset parameters, and no bootstrap-version rule. That means
the template is a plain CloudFormation document env0 can deploy directly, with
no `cdk bootstrap` step required.
"""
import os

import aws_cdk as cdk

from western_union_poc.fargate_stack import FargatePocStack

# Honor CDK_OUTDIR when present (set by scripts/synth.sh and by the cdk CLI),
# otherwise default to ./synth so the output path matches the env0 template's
# "CloudFormation file" setting.
app = cdk.App(outdir=os.environ.get("CDK_OUTDIR") or "synth")

FargatePocStack(
    app,
    "WesternUnionCdkPoc",
    synthesizer=cdk.CliCredentialsStackSynthesizer(),
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=(
            os.environ.get("CDK_DEFAULT_REGION")
            or os.environ.get("AWS_REGION")
            or "us-east-1"
        ),
    ),
    description="env0 + AWS CDK POC: ALB-fronted Fargate service (Western Union demo).",
)

app.synth()
