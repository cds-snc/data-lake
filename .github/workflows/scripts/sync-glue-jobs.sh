#!/bin/bash
set -euo pipefail

#
# Checks if there are changes to the Glue ETL jobs and creates a PR if yes.
# This script will update an existing PR if the branch already exists.
#

JOB_DIR="./terragrunt/aws/glue/etl"
REMOTE_REPO="origin"
BRANCH_NAME="chore/glue-job-sync"
BASE_BRANCH="main"
PR_TITLE="chore: automated glue job sync"
PR_BODY="## Summary
Automated sync of AWS Glue ETL jobs."

# Check for changes in the repository
if git diff-index --quiet HEAD -- "$JOB_DIR"; then
    echo "No changes detected."
    exit 0
else
    echo "Changes detected."
fi

# Check if the remote branch exists
git fetch "$REMOTE_REPO"
if git ls-remote --heads "$REMOTE_REPO" "$BRANCH_NAME" | grep -q "$BRANCH_NAME"; then
    echo "Branch '$BRANCH_NAME' exists. Checking out and updating."
    git stash
    git checkout "$BRANCH_NAME"
    git stash pop
else
    echo "Branch '$BRANCH_NAME' does not exist. Creating new branch."
    git checkout -b "$BRANCH_NAME" "$BASE_BRANCH"
fi

# Add changes and commit
git config user.email "github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"
git add "$JOB_DIR"
git commit -m "$PR_TITLE"

# Push branch and create the PR
git push "$REMOTE_REPO" "$BRANCH_NAME"
gh pr create --base "$BASE_BRANCH" --head "$BRANCH_NAME" --title "$PR_TITLE" --body "$PR_BODY"