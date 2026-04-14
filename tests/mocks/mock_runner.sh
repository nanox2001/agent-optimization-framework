#!/bin/bash
# Mock experiment runner for testing
CONFIG_FILE="$1"
VARIANT_ID="$2"

# Simulate different behaviors based on variant
if [[ "$VARIANT_ID" == *"slow"* ]]; then
    sleep 5
elif [[ "$VARIANT_ID" == *"error"* ]]; then
    echo "Error: Simulated failure" >&2
    exit 1
fi

# Output metrics JSON
cat << EOF
{
  "scenario": "web_scrape",
  "primary_metric": "accuracy",
  "values": {
    "success_rate": 0.95,
    "accuracy": 0.88,
    "completeness": 0.92,
    "execution_time_sec": 125.5
  },
  "metadata": {
    "variant": "$VARIANT_ID",
    "test_cases": 100,
    "passed": 95
  }
}
EOF
exit 0