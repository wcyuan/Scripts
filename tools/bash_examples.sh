#!/bin/bash
#

# change to 1 to turn on dry run
FLAGS_dry_run=0
function run() {
  if (( $FLAGS_dry_run ))
  then
    echo "DRY RUN: " "$@"
  else
    "$@"
  fi
}

# https://unix.stackexchange.com/questions/145651/using-exec-and-tee-to-redirect-logs-to-stdout-and-a-log-file-in-the-same-time
function save_output_to_log() {
  readonly LOG_FILE="run_pipeline.$(date +%Y%m%d-%H%M%S).log"
  touch "$LOG_FILE"
  exec &> >(tee -a "$LOG_FILE")
  echo "Saving all output to $LOG_FILE"
}
save_output_to_log

echo stdout
echo stderr >&2
