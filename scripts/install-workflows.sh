#!/bin/bash
# Move workflow files to .github/workflows/
# Run this script with a token that has the 'workflows' scope:
#   git checkout claude-code/backend-scaffold/a7f2e9c1
#   bash scripts/install-workflows.sh
#   git add .github/workflows/ && git commit -m "Install CI/CD workflows" && git push

set -e

mkdir -p .github/workflows
cp workflows/ci.yml .github/workflows/ci.yml
cp workflows/deploy.yml .github/workflows/deploy.yml
cp workflows/migrate.yml .github/workflows/migrate.yml
cp workflows/release.yml .github/workflows/release.yml

echo "Workflows installed to .github/workflows/"
echo "Commit and push with a token that has the 'workflows' scope."
