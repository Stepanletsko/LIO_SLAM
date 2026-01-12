# Author: Stepan Letsko
# Date: January 10, 2026
# Purpose: This Dockerfile builds a reproducible environment for the Thesis project.
#          It sets up ROS 2 Humble, installs necessary dependencies for FAST_LIO and Livox drivers,
#          and prepares the workspace for building and running the SLAM system.

# Start from the official ROS 2 Humble base image (contains minimal ROS installation)
FROM ros:humble-ros-base

# 1. Install basic tools and dependencies for FAST_LIO
# Update package lists and install packages with automatic 'yes' to prompts
RUN apt-get update && apt-get install -y --fix-missing \
    git \
    # git: Version control system to clone repositories
    cmake \
    # cmake: Cross-platform build system generator used by ROS packages
    build-essential \
    # build-essential: Contains GCC/G++ compilers and Make tool
    libpcl-dev \
    # libpcl-dev: Point Cloud Library development files (headers/libs) for 3D processing
    ros-humble-pcl-ros \
    # ros-humble-pcl-ros: ROS 2 interface for PCL, allows PCL types in ROS nodes
    ros-humble-pcl-conversions \
    # ros-humble-pcl-conversions: Utilities to convert between ROS PointCloud2 messages and PCL objects
    ros-humble-libpointmatcher \
    # ros-humble-libpointmatcher: Library for Iterative Closest Point (ICP) matching
    ros-humble-rviz2 \
    # ros-humble-rviz2: 3D visualization tool for ROS 2 (to see the map and lidar data)
    && rm -rf /var/lib/apt/lists/*
    # Clean up the apt cache to keep the Docker image size small

# 2. Install Livox-SDK2 (Required by livox_ros_driver2)
# We clone and install it into the system folders of the container manually
# because it is not available as a standard apt package.
RUN git clone https://github.com/Livox-SDK/Livox-SDK2.git /tmp/Livox-SDK2 && \
    # Clone the SDK source code to a temporary directory
    cd /tmp/Livox-SDK2 && \
    # Enter the directory
    mkdir build && cd build && \
    # Create a build directory and enter it (standard CMake practice)
    cmake .. && make -j$(nproc) && make install && \
    # Configure with CMake, compile using all available CPU cores, and install to system paths
    rm -rf /tmp/Livox-SDK2
    # Remove the source code to save space after installation

# 3. Setup the environment
# Set the default working directory inside the container to the ROS workspace root
WORKDIR /root/ros2_ws

# Add the ROS 2 setup script to .bashrc so it is sourced automatically
# whenever a new terminal is opened inside the container.
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# 4. Install Colcon (Build tool)
# Update apt again (good practice before new install block) and install colcon
# python3-colcon-common-extensions: The standard build tool for ROS 2 workspaces
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    && pip3 install rosbags
