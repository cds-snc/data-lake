#!/bin/bash
set -euo pipefail

#
# Retrieves all the AWS glue jobs and creates a directory structure
# based on the job name. The job details are saved in a JSON file.
#
# It is expected that the job name will be in the following format:
# Business Unit / Product / Environment / Job Name
#

aws glue get-jobs --query 'Jobs[].Name' --output text |
while IFS= read -r name; do
  # Split the name on '/'
  IFS='/' read -ra segments <<< "$name"

  # Initialize directory path
  dir_path=""
  filename=""

  # Get the number of segments
  num_segments=${#segments[@]}

  # Process all segments except the last one to build the directory path
  for ((i=0; i<num_segments; i++)); do
    segment="${segments[i]}"
    segment=$(echo "$segment" | xargs)
    segment=$(echo "$segment" | sed 's/ /-/g' | tr '[:upper:]' '[:lower:]')

    if [ $i -eq $((num_segments-1)) ]; then
      filename="$segment.json"
    else
      dir_path="$dir_path/$segment"
    fi
  done

  dir_path="./terragrunt/aws/glue/etl/${dir_path}"

  mkdir -p "$dir_path"
  aws glue get-job --job-name "$name" --output json > "$dir_path/$filename"

  echo "Created file: $dir_path/$filename"
done