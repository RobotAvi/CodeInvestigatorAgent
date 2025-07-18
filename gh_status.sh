#!/usr/bin/env bash
set -ex

echo "$GH_TOKEN" | gh auth login --with-token
gh run list