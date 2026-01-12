#!/bin/bash

# Author: Stepan Letsko
# Date: January 12, 2026
# Purpose: Automates the FAST_LIO mapping process.
#          1. Launches the SLAM node in the background.
#          2. Plays the ROS 2 bag.
#          3. Calls the service to save the PCD map.
#          4. Stops the SLAM node.

# Function to monitor the actual file size growing
monitor_file_growth() {
    local pid=$1
    local file_path="/root/ros2_ws/bags/outdoor_scan.pcd"
    
    echo "Saving Map to $file_path..."
    echo "Monitoring file size..."
    
    while kill -0 $pid 2> /dev/null; do
        if [ -f "$file_path" ]; then
            # Get human readable size (e.g., 15M, 100M)
            size=$(du -h "$file_path" | cut -f1)
            echo -ne "Current file size: $size   \r"
        fi
        sleep 0.5
    done
    echo -e "\nDone!"
}

# Check if bag name is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: ./run_mapping.sh <bag_folder_name>"
    echo "Example: ./run_mapping.sh outdoor_Mainbuilding_ros2"
    exit 1
fi

BAG_NAME=$1

# Source the ROS 2 workspace to ensure custom messages and packages are found
source /root/ros2_ws/install/setup.bash

# 1. Launch FAST_LIO in the background
echo "Starting FAST_LIO..."
# We redirect output to a log file to keep the terminal clean for the bag status
ros2 launch fast_lio mapping.launch.py config_file:=avia.yaml > /root/ros2_ws/log/fast_lio_run.log 2>&1 &
LIO_PID=$!

# Wait a few seconds for the node to initialize
sleep 5

# 2. Play the bag
echo "Playing bag: $BAG_NAME..."
ros2 bag play "$BAG_NAME"

# Wait a moment to ensure final messages are processed
sleep 2

# 3. Save the map
echo "Bag finished. Requesting map save..."

# Run the service call in the background so we can show a spinner
ros2 service call /map_save std_srvs/srv/Trigger "{}" > /root/ros2_ws/log/map_save.log 2>&1 &
SAVE_PID=$!

# Monitor the file size while waiting
monitor_file_growth $SAVE_PID

# 4. Cleanup
echo "Stopping FAST_LIO..."
kill $LIO_PID

echo "Done! Map should be at: bags/outdoor_scan.pcd"