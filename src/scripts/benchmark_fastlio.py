# Author: Stepan Letsko
# Date: January 15, 2026
# Purpose: This script benchmarks FAST_LIO performance by running a ROS 2 bag and parsing the logs.
#          It calculates average processing times and saves the results to CSV and log files.

import subprocess  # Import subprocess to run shell commands
import re  # Import re for regular expression matching
import os  # Import os for operating system dependent functionality
import csv  # Import csv for reading and writing CSV files
import time  # Import time for time-related functions
import sys  # Import sys for system-specific parameters and functions
import signal # Import signal for SIGINT
from pathlib import Path  # Import Path for object-oriented filesystem paths

def run_benchmark(bag_path, config="avia.yaml"):  # Define the main benchmark function taking bag path and config file
    # 1. Setup Paths - Directing to your specific results folder
    bag_name = Path(bag_path).stem  # Extract the filename without extension from the bag path
    
    # Absolute path to your desired results directory
    base_results_path = Path("/root/ros2_ws/src/results")  # Define the base directory for storing results
    results_dir = base_results_path / f"{bag_name}_timing_results"  # Create a specific directory for this bag's results
    
    # Create the directories if they don't exist
    results_dir.mkdir(parents=True, exist_ok=True)  # Create the directory structure, ignoring if it already exists
    
    log_file_path = results_dir / f"{bag_name}_log.txt"  # Define the path for the log file
    csv_file_path = results_dir / f"{bag_name}_data.csv"  # Define the path for the CSV data file
    
    # 2. Get bag duration for progress bar
    print(f" Analyzing bag: {bag_name}...")  # Print status message
    info_proc = subprocess.run(['ros2', 'bag', 'info', bag_path], capture_output=True, text=True)  # Run 'ros2 bag info' to get bag metadata
    duration_match = re.search(r"Duration:\s+(\d+\.\d+)s", info_proc.stdout)  # Search for the duration in the output using regex
    if not duration_match:  # Check if duration was found
        print("Could not determine bag duration. Check if the bag path is correct.")  # Print error if not found
        return  # Exit the function
    total_duration = float(duration_match.group(1))  # Parse the duration string to a float

    # 3. Open files
    log_file = open(log_file_path, "w")  # Open the log file for writing
    csv_file = open(csv_file_path, "w", newline="")  # Open the CSV file for writing
    csv_writer = csv.writer(csv_file)  # Create a CSV writer object
    csv_writer.writerow(["IMU_Map_Downsample", "ave_match", "ave_solve", "ave_ICP", "map_incre", "ave_total", "icp", "construct_H"])  # Write the header row to the CSV

    # 4. Start FAST-LIO
    print(f"Launching FAST-LIO with config: {config}")  # Print launch status
    # Using stdbuf to prevent output buffering so we can parse logs in real-time
    mapping_cmd = ['stdbuf', '-oL', 'ros2', 'launch', 'fast_lio', 'mapping.launch.py', f'config_file:={config}', 'rviz:=false']  # Construct the launch command
    mapping_proc = subprocess.Popen(mapping_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)  # Start the process, capturing stdout
   
    # === ADDING THIS BLOCK TO FIX THE STARTUP DROP ISSUE ===
    print("Waiting 20 seconds for node to initialise...")
    time.sleep(20) 
   

    # 5. Start Bag Playback (Removed 
    print(f" Playing bag...")  # Print playback status
    bag_cmd = ['ros2', 'bag', 'play', bag_path]  # Construct the bag play command
    # Redirect bag output to DEVNULL so it doesn't clutter the progress bar
    subprocess.Popen(bag_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # Start bag playback in background, silencing output

    # 6. Monitor and Parse
    start_time = time.time()  # Record the start time
    latencies = []  # Initialize list to store latency values
    
    print(f"Benchmarking in progress...")  # Print benchmark status
    
    try:  # Start try block to handle interruptions
        while True:  # Loop continuously
            line = mapping_proc.stdout.readline()  # Read a line from the FAST-LIO process output
            if not line: break  # Break loop if no more output (process ended)
            
            if "ave total:" in line:  # Check if the line contains timing information
                log_file.write(line)  # Write the raw line to the log file
                # Regex to grab the timing values
                pattern = r"Downsample:\s*([\d\.]+).*match:\s*([\d\.]+).*solve:\s*([\d\.]+).*ICP:\s*([\d\.]+).*incre:\s*([\d\.]+).*total:\s*([\d\.]+).*icp:\s*([\d\.]+).*H:\s*([\d\.]+)"  # Define regex pattern for metrics
                match = re.search(pattern, line)  # Search for pattern in the line
                
                if match:  # If pattern matches
                    vals = [float(x) for x in match.groups()]  # Convert matched groups to floats
                    csv_writer.writerow(vals)  # Write values to CSV
                    latencies.append(vals[5]) # ave_total  # Append total time to latencies list
            
            if "DIAGNOSTIC" in line or "Buffer Clears" in line or "Received Msgs" in line or "Processed Frames" in line:
                print(f"\r{line.strip()}")
            
            # Update Progress Bar based on elapsed wall time
            elapsed = time.time() - start_time  # Calculate elapsed time
            percent = min(100, (elapsed / total_duration) * 100)  # Calculate percentage complete
            bar = "█" * int(percent / 2) + "-" * (50 - int(percent / 2))  # Create progress bar string
            sys.stdout.write(f"\r|{bar}| {percent:.1f}% Complete")  # Print progress bar with carriage return
            sys.stdout.flush()  # Flush stdout to ensure immediate display
            
            if elapsed > total_duration + 5: # Small buffer for SLAM cleanup  # Check if time exceeded duration plus buffer
                break  # Break the loop

    except KeyboardInterrupt:  # Handle Ctrl+C interruption
        print("\n\nStopping benchmark...")  # Print stopping message
    finally:  # Execute cleanup code
        # Graceful shutdown to allow destructor to print stats
        if mapping_proc.poll() is None:
            mapping_proc.send_signal(signal.SIGINT)
            try:
                # Read remaining output (stats) while waiting for exit
                while mapping_proc.poll() is None:
                    line = mapping_proc.stdout.readline()
                    if not line: break
                    if "DIAGNOSTIC" in line or "Buffer Clears" in line or "Received Msgs" in line or "Processed Frames" in line:
                        print(f"\r{line.strip()}")
            except:
                mapping_proc.terminate()
        
        log_file.close()  # Close the log file
        csv_file.close()  # Close the CSV file

   # 7. Final Statistics
    if latencies:  # Check if any latency data was collected
        avg_v = sum(latencies) / len(latencies)  # Calculate average latency
        max_v = max(latencies)  # Find maximum latency
        min_v = min(latencies)  # Find minimum latency
        
        summary = (  # Create summary string
            f"===============================================\n"
            f"   FINAL STATISTICS: {bag_name}\n"
            f"===============================================\n"
            f"Average Processing Time: {avg_v:.6f} s ({avg_v*1000:.2f} ms)\n"
            f"Maximum (Peak) Time:     {max_v:.6f} s ({max_v*1000:.2f} ms)\n"
            f"Minimum Time:            {min_v:.6f} s ({min_v*1000:.2f} ms)\n"
            f"Total Frames Processed:  {len(latencies)}\n"
            f"===============================================\n\n"
        )
        
        # Read the current log content (the raw lines)
        with open(log_file_path, "r") as f:  # Open log file for reading
            original_content = f.read()  # Read existing content
            
        # Write the summary first, then the original content
        with open(log_file_path, "w") as f:  # Open log file for writing (overwriting)
            f.write(summary + "--- RAW LOG DATA ---\n" + original_content)  # Write summary followed by original content
            
        print(summary)  # Print summary to console
        print(f"✅ Results saved to: {results_dir}")  # Print save location

if __name__ == "__main__":  # Check if script is run directly
    bag = sys.argv[1] if len(sys.argv) > 1 else "bags/outdoor_Mainbuilding_ROS2"  # Get bag path from args or default
    cfg = sys.argv[2] if len(sys.argv) > 2 else "avia.yaml"  # Get config from args or default
    run_benchmark(bag, cfg)  # Run the benchmark function