#!/bin/bash

# Author: Stepan Letsko
# Date: January 12, 2026
# Purpose: This script converts ROS 1 bag files to ROS 2 format using rosbags-convert.
#          It automatically patches the generated metadata.yaml file to fix QoS profile errors
#          and updates Livox message types to be compatible with the ROS 2 driver (livox_ros_driver2).

# Check if the number of arguments provided is not equal to 1
if [ "$#" -ne 1 ]; then
    # Print usage instructions if the argument count is incorrect
    echo "Usage: ./convert_bag.sh <input_bag.bag>"
    # Exit the script with an error code (1)
    exit 1
fi

# Store the first argument as the input filename
INPUT_FILE=$1

# Create the output directory name by removing the file extension from the input filename
# For example, 'my_data.bag' becomes 'my_data'
OUTPUT_DIR="${INPUT_FILE%.*}" 

# Print a message indicating the start of the conversion process
echo "Converting $INPUT_FILE to $OUTPUT_DIR..."

# Execute the rosbags-convert tool with the source file and destination directory
rosbags-convert --src "$INPUT_FILE" --dst "$OUTPUT_DIR"

# Check the exit status of the previous command (rosbags-convert)
# $? stores the exit code; 0 means success
if [ $? -eq 0 ]; then
    # If conversion was successful, print a status message
    echo "Conversion finished. Applying fixes to metadata.yaml..."
    
    # Define the path to the metadata.yaml file inside the new output directory
    METADATA_PATH="$OUTPUT_DIR/metadata.yaml"
    
    # Check if the metadata.yaml file actually exists
    if [ -f "$METADATA_PATH" ]; then
        # Fix 1: Use sed to replace the 'offered_qos_profiles' field.
        # The conversion tool often outputs invalid YAML for this field (e.g., complex lists).
        # We replace it with an empty string "" to prevent "bad conversion" errors in ROS 2.
        sed -i 's/offered_qos_profiles: .*/offered_qos_profiles: ""/g' "$METADATA_PATH"
        
        # Fix 2: Use sed to update the message type definition.
        # The ROS 1 bag uses 'livox_ros_driver', but our ROS 2 workspace uses 'livox_ros_driver2'.
        # This ensures the topic type matches what FAST_LIO expects.
        sed -i 's/livox_ros_driver\/msg\/CustomMsg/livox_ros_driver2\/msg\/CustomMsg/g' "$METADATA_PATH"
        
        # Print a success message indicating the bag is ready to use
        echo "Success! Bag converted and patched: $OUTPUT_DIR"
    else
        # If metadata.yaml is missing, print an error message
        echo "Error: metadata.yaml not found in output directory."
    fi
else
    # If rosbags-convert returned a non-zero exit code, print a failure message
    echo "Conversion failed."
    # Exit the script with an error code (1)
    exit 1
fi