#!/usr/bin/env bash
# Delete the whole environment (stops Learner Lab spend). Artefact bucket is kept.
set -euo pipefail
STACK_NAME="${STACK_NAME:-devops-demo}"
aws cloudformation delete-stack --stack-name "$STACK_NAME"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"
echo "Stack $STACK_NAME deleted."
