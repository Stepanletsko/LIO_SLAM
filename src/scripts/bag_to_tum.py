import sys
from pathlib import Path
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py

def get_rosbag_options(path, storage_id='sqlite3'):
    storage_options = rosbag2_py.StorageOptions(uri=path, storage_id=storage_id)
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr')
    return storage_options, converter_options

def extract_odometry(bag_path, output_file, topic_name='/Odometry'):
    print(f"Reading: {bag_path}")
    
    # Handle both direct file (.db3) or folder path inputs
    bag_path_obj = Path(bag_path)
    if bag_path_obj.is_file():
        read_path = str(bag_path_obj.parent) # ROS 2 reader needs the folder
    else:
        read_path = str(bag_path_obj)

    try:
        storage_opts, converter_opts = get_rosbag_options(read_path)
        reader = rosbag2_py.SequentialReader()
        reader.open(storage_opts, converter_opts)
    except Exception as e:
        print(f"Error opening bag: {e}")
        return

    # Dynamic topic type discovery
    topic_types = reader.get_all_topics_and_types()
    type_map = {t.name: t.type for t in topic_types}
    
    if topic_name not in type_map:
        print(f"Error: Topic '{topic_name}' not found.")
        print(f"Available topics: {list(type_map.keys())}")
        return

    msg_type_str = type_map[topic_name]
    msg_class = get_message(msg_type_str)

    # Filter for our topic
    storage_filter = rosbag2_py.StorageFilter(topics=[topic_name])
    reader.set_filter(storage_filter)

    print(f"Extracting {topic_name} to {output_file}...")
    
    count = 0
    with open(output_file, 'w') as f:
        while reader.has_next():
            (topic, data, t) = reader.read_next()
            msg = deserialize_message(data, msg_class)
            
            # Format: timestamp tx ty tz qx qy qz qw
            # Time must be in seconds (float)
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            
            tx = msg.pose.pose.position.x
            ty = msg.pose.pose.position.y
            tz = msg.pose.pose.position.z
            qx = msg.pose.pose.orientation.x
            qy = msg.pose.pose.orientation.y
            qz = msg.pose.pose.orientation.z
            qw = msg.pose.pose.orientation.w
            
            f.write(f"{timestamp:.6f} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n")
            count += 1

    print(f"Done! Extracted {count} poses.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 bag_to_tum.py [BAG_PATH] [OUTPUT_FILENAME]")
    else:
        # Default topic is /Odometry, but you can change it in the function call if needed
        extract_odometry(sys.argv[1], sys.argv[2])
