import sys
import os
import argparse
import subprocess
import importlib

def ensure_dependencies():
    """Automatically installs working libraries to a local folder to avoid system conflicts."""
    # Create a local hidden folder for libs next to this script
    lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".libs")
    
    # Prioritize this folder in python path
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    
    try:
        import rosbags.ros1
    except ImportError:
        print(f"Installing standalone dependencies to {lib_dir}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--target", lib_dir,
            "--upgrade",
            "rosbags==0.9.16", "lz4", "numpy<2.0"
        ])
        print("Dependencies ready. Restarting script...")
        # Re-execute the script to ensure the new packages are loaded correctly
        os.execv(sys.executable, [sys.executable] + sys.argv)

# Define the Livox CustomMsg structure (matches both driver versions)
LIVOX_MSG_DEF = """
std_msgs/Header header
uint64 timebase
uint32 point_num
uint8 lidar_id
uint8[3] rsvd
CustomPoint[] points
================================================================================
MSG: livox_ros_driver/CustomPoint
uint32 offset_time
float32 x
float32 y
float32 z
uint8 reflectivity
uint8 tag
uint8 line
"""

def main():
    # 1. Ensure libraries are present before importing them
    ensure_dependencies()

    # 2. Import libraries (now guaranteed to work)
    from rosbags.ros1 import Reader
    from rosbags.ros2 import Writer
    from rosbags.serde import deserialize_ros1, serialize_cdr
    from rosbags.typesys import get_types_from_msg, register_types, get_typestore, stores

    parser = argparse.ArgumentParser(description='Convert Livox ROS1 bag to ROS2 with type renaming.')
    parser.add_argument('--src', required=True, help='Source ROS1 bag file')
    parser.add_argument('--dst', help='Destination ROS2 bag directory (optional)')
    args = parser.parse_args()

    # 3. Register the OLD type name so we can read the ROS 1 bag
    register_types(get_types_from_msg(LIVOX_MSG_DEF, 'livox_ros_driver/msg/CustomMsg'))

    # 4. Register the NEW type name so we can write the ROS 2 bag
    # We replace the package name in the definition to match livox_ros_driver2
    ros2_def = LIVOX_MSG_DEF.replace('livox_ros_driver', 'livox_ros_driver2')
    register_types(get_types_from_msg(ros2_def, 'livox_ros_driver2/msg/CustomMsg'))

    typestore = get_typestore(stores.ros2)
    
    # Input and Output filenames
    src = args.src
    if args.dst:
        dst = args.dst
    else:
        dst = src.replace('.bag', '') + '_fixed_ros2'

    print(f"Converting {src} -> {dst}...")

    with Reader(src) as reader, Writer(dst) as writer:
        conn_map = {}
        for conn, timestamp, data in reader.messages():
            topic = conn.topic
            msg_type = conn.msgtype

            # If this is the LiDAR topic, swap the type to the new driver
            if msg_type == 'livox_ros_driver/msg/CustomMsg':
                msg_type = 'livox_ros_driver2/msg/CustomMsg'
                msg = deserialize_ros1(data, 'livox_ros_driver/msg/CustomMsg')
                data = serialize_cdr(msg, msg_type, typestore)
            else:
                # Convert standard messages (IMU, etc.)
                msg = deserialize_ros1(data, msg_type)
                data = serialize_cdr(msg, msg_type, typestore)

            if topic not in conn_map:
                conn_map[topic] = writer.add_connection(topic, msg_type, typestore=typestore)
            writer.write(conn_map[topic], timestamp, data)

    print(f"Done! You can now play: ros2 bag play {dst}")

if __name__ == '__main__':
    main()