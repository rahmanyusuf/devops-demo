#!/usr/bin/env bash
# Fallback: run the same steps as the pipeline from your own terminal.
# Requires: AWS CLI configured with the Learner Lab credentials (us-east-1).
set -euo pipefail
cd "$(dirname "$0")/.."

STACK_NAME="${STACK_NAME:-devops-demo}"
REGION="${AWS_REGION:-us-east-1}"
SHORT_SHA="$(git rev-parse --short=7 HEAD 2>/dev/null || date +%s)"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="devops-demo-artifacts-${ACCOUNT_ID}"

echo "== Test =="; python -m pytest -q
echo "== Lint IaC =="; cfn-lint infra/template.yaml

echo "== Build =="
echo "$SHORT_SHA" > app/VERSION
mkdir -p build && rm -f build/app.zip
(cd app && zip -r ../build/app.zip app.py requirements.txt VERSION)

echo "== Publish =="
aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null || aws s3 mb "s3://$BUCKET" --region "$REGION"
aws s3 cp build/app.zip "s3://$BUCKET/releases/${SHORT_SHA}.zip"

echo "== Deploy =="
aws cloudformation deploy --region "$REGION" \
  --template-file infra/template.yaml --stack-name "$STACK_NAME" \
  --parameter-overrides ArtifactBucket="$BUCKET" \
    ArtifactKey="releases/${SHORT_SHA}.zip" AppVersion="$SHORT_SHA" \
  --no-fail-on-empty-changeset

aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerURL'].OutputValue" --output text
