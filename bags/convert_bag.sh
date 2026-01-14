#!/bin/bash

# Author: Stepan Letsko
# Date: January 12, 2026
# Purpose: Converts ROS 1 bag files to ROS 2 (Humble) format with strict metadata patching.
#          Fixes the 'bad conversion' yaml-cpp error by serializing QoS profiles.

if [ "$#" -ne 1 ]; then
    echo "Usage: ./convert_bag.sh <input_bag.bag>"
    exit 1
fi

INPUT_FILE=$1
OUTPUT_DIR="${INPUT_FILE%.*}" 

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File $INPUT_FILE not found."
    exit 1
fi

# 1. Install Dependencies
if ! command -v pip3 &> /dev/null; then
    apt-get update && apt-get install -y python3-pip
fi
pip3 install rosbags ruamel.yaml

# 2. Conversion Process
TEMP_DIR="/root/tmp_$(basename "$OUTPUT_DIR")"
rm -rf "$TEMP_DIR"
INPUT_SIZE=$(du -k "$INPUT_FILE" | cut -f1)

echo "Converting $INPUT_FILE to temporary location $TEMP_DIR..."
rosbags-convert --src "$INPUT_FILE" --dst "$TEMP_DIR" > /tmp/conversion_log.txt 2>&1 &
PID=$!

while kill -0 $PID 2> /dev/null; do
    if [ -d "$TEMP_DIR" ]; then
        OUTPUT_SIZE=$(du -sk "$TEMP_DIR" | cut -f1)
        PERCENT=$(( 100 * OUTPUT_SIZE / INPUT_SIZE ))
        [ "$PERCENT" -gt 100 ] && PERCENT=100
        printf "\r[%-50s] %d%%" $(printf "#%.0s" $(seq 1 $((PERCENT/2)))) "$PERCENT"
    fi
    sleep 1
done
wait $PID

if [ $? -ne 0 ]; then
    echo -e "\nConversion failed. Check /tmp/conversion_log.txt"
    exit 1
fi

# 3. Apply Humble-Specific Metadata Fixes
echo -e "\nApplying 'Nuclear Fix' to metadata.yaml for ROS 2 Humble..."
METADATA_PATH="$TEMP_DIR/metadata.yaml"

python3 -c "
import yaml
from ruamel.yaml import YAML

yaml_ruamel = YAML()
yaml_ruamel.preserve_quotes = True
file_path = '$METADATA_PATH'

# Humble requires QoS profiles as a serialized string, not a nested YAML object.
tf_qos_list = [{
    'history': 1,
    'depth': 1,
    'reliability': 1,
    'durability': 2,
    'deadline': {'sec': 2147483647, 'nsec': 4294967295},
    'lifespan': {'sec': 2147483647, 'nsec': 4294967295},
    'liveliness': 1,
    'liveliness_lease_duration': {'sec': 2147483647, 'nsec': 4294967295},
    'avoid_ros_namespace_conventions': False
}]

# Generate the serialized string that Humble's yaml-cpp parser expects
tf_qos_string = yaml.dump(tf_qos_list, default_flow_style=False)

with open(file_path, 'r') as f:
    data = yaml_ruamel.load(f)

# Fix 1: Ensure storage_identifier is never empty (Fixes line 7 error)
data['rosbag2_bagfile_information']['storage_identifier'] = 'sqlite3'

# Fix 2: Loop through topics and sanitize QoS profiles
for topic in data['rosbag2_bagfile_information']['topics_with_message_count']:
    meta = topic['topic_metadata']
    if meta['name'] == '/tf_static':
        meta['offered_qos_profiles'] = tf_qos_string
    else:
        # Default empty string prevents conversion errors for standard topics
        meta['offered_qos_profiles'] = ''

with open(file_path, 'w') as f:
    yaml_ruamel.dump(data, f)
"

# 4. Final Cleanup
# Update message type in case any Livox topics exist (for project compatibility)
sed -i 's/livox_ros_driver\/msg\/CustomMsg/livox_ros_driver2\/msg\/CustomMsg/g' "$METADATA_PATH"

rm -rf "$OUTPUT_DIR"
mv "$TEMP_DIR" "$OUTPUT_DIR"
echo "Success! Bag converted and patched: $OUTPUT_DIR"