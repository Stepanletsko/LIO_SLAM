FROM ros:humble-ros-base

# 1. Install basic tools and dependencies for FAST_LIO
RUN apt-get update && apt-get install -y --fix-missing \
    git \
    cmake \
    build-essential \
    libpcl-dev \
    ros-humble-pcl-ros \
    ros-humble-pcl-conversions \
    ros-humble-libpointmatcher \
    ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Livox-SDK2 (Required by livox_ros_driver2)
# We clone and install it into the system folders of the container
RUN git clone https://github.com/Livox-SDK/Livox-SDK2.git /tmp/Livox-SDK2 && \
    cd /tmp/Livox-SDK2 && \
    mkdir build && cd build && \
    cmake .. && make -j$(nproc) && make install && \
    rm -rf /tmp/Livox-SDK2

# 3. Setup the environment
WORKDIR /root/ros2_ws
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# 4. Install Colcon (Build tool)
RUN apt-get update && apt-get install -y python3-colcon-common-extensions
