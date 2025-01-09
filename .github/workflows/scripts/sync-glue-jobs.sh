#!/bin/bash
set -euo pipefail

#
# Checks if there are changes to the Glue ETL jobs and creates a PR if yes.
# This script will update an existing PR if the branch already exists.
#

CREATE_PR="true"
JOB_DIR="./terragrunt/aws/glue/etl"
REMOTE_REPO="origin"
BRANCH_NAME="chore/glue-job-sync"
BASE_BRANCH="main"
PR_TITLE="chore: automated glue job sync"
PR_BODY="## Summary
Automated sync of AWS Glue ETL jobs."

# Check if the remote branch exists
if git ls-remote --heads "$REMOTE_REPO" "$BRANCH_NAME" | grep -q "$BRANCH_NAME"; then
    echo "Branch '$BRANCH_NAME' exists. Checking out."
    git checkout "$BRANCH_NAME"
    CREATE_PR="false"
else
    echo "Branch '$BRANCH_NAME' does not exist. Creating new branch."
    git fetch "$REMOTE_REPO" "$BASE_BRANCH"
    git checkout -b "$BRANCH_NAME" "$REMOTE_REPO/$BASE_BRANCH"
fi

echo "Syncing Glue jobs..."
.github/workflows/scripts/get-glue-jobs.sh

# Check for changes in the branch
if git diff-index --quiet HEAD -- "$JOB_DIR"; then
    echo "No changes detected."
    exit 0
else
    echo "Changes detected:"
    git diff -- "$JOB_DIR"
    git push "$REMOTE_REPO" "$BRANCH_NAME"
fi

# Commit changes through the GitHub API so the commits are signed
echo "Committing changes..."
FILES_CHANGED="$(git status --porcelain | awk '{print $2}')"
for FILE in $FILES_CHANGED; do
    echo "Committing $FILE..."
    MESSAGE="chore: regenerate $(basename "$FILE") for $(date -u '+%Y-%m-%d')"
    SHA="$(git rev-parse $BRANCH_NAME:"$FILE" || echo "")"
    gh api --method PUT /repos/cds-snc/data-lake/contents/"$FILE" \
        --field message="$MESSAGE" \
        --field content="$(base64 -w 0 "$FILE")" \
        --field encoding="base64" \
        --field branch="$BRANCH_NAME" \
        --field sha="$SHA"
done

# Create the PR if it doesn't already exist
if [ "$CREATE_PR" = "true" ]; then
    echo "Creating PR..."
    gh pr create --base "$BASE_BRANCH" --head "$BRANCH_NAME" --title "$PR_TITLE" --body "$PR_BODY"
fi
