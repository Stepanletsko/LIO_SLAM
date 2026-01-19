import subprocess
import re
import os
import time
import sys
import signal
import psutil
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def get_mapping_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and 'fastlio_mapping' in ' '.join(proc.info['cmdline']):
            return proc.info['pid']
    return None

def run_profile(bag_path, config="avia.yaml"):
    # 1. Setup Paths
    bag_name = Path(bag_path).stem
    results_dir = Path("/root/ros2_ws/src/results/resource_analysis")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Get bag duration for progress bar
    info_proc = subprocess.run(['ros2', 'bag', 'info', bag_path], capture_output=True, text=True)
    duration_match = re.search(r"Duration:\s+(\d+\.\d+)s", info_proc.stdout)
    total_duration = float(duration_match.group(1)) if duration_match else 0

    # 3. Start FAST-LIO
    print(f"🚀 Launching FAST-LIO (Profiling Mode)...")
    mapping_launch = subprocess.Popen(['ros2', 'launch', 'fast_lio', 'mapping.launch.py', 
                                     f'config_file:={config}', 'use_sim_time:=true', 'rviz:=false'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    mapping_pid = None
    while mapping_pid is None:
        time.sleep(1)
        mapping_pid = get_mapping_pid()
    
    p = psutil.Process(mapping_pid)

    # 4. Start Playback
    play_proc = subprocess.Popen(['ros2', 'bag', 'play', bag_path, '--clock'], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # 5. Monitoring Loop with Progress Bar
    stats = []
    start_time = time.time()
    print(f"📊 Monitoring Resources for: {bag_name}")
    
    try:
        while play_proc.poll() is None:
            elapsed = time.time() - start_time
            
            # Capture Metrics
            cpu = p.cpu_percent(interval=None) 
            ram = p.memory_info().rss / (1024 * 1024)
            stats.append([elapsed, cpu, ram])
            
            # Progress Bar Logic
            percent = min(100, (elapsed / total_duration) * 100) if total_duration > 0 else 0
            bar = "█" * int(percent // 2) + "-" * (50 - int(percent // 2))
            
            status = f"\r|{bar}| {percent:.1f}% | CPU: {cpu:5.1f}% | RAM: {ram:6.1f} MB"
            sys.stdout.write(status)
            sys.stdout.flush()
            
            time.sleep(1)
            
        sys.stdout.write(f"\r|{'█' * 50}| 100.0% | Done!                           \n")

    finally:
        os.kill(mapping_launch.pid, signal.SIGINT)
        time.sleep(2)

    # 6. Final Plotting & Statistics Summary
    df = pd.DataFrame(stats, columns=['Time', 'CPU', 'RAM'])
    df.to_csv(results_dir / f"{bag_name}_resources.csv", index=False)
    
    # Calculate statistics
    peak_cpu = df['CPU'].max()
    avg_cpu = df['CPU'].mean()
    peak_ram = df['RAM'].max()
    final_ram = df['RAM'].iloc[-1]

    # Display Summary
    print("\n" + "="*40)
    print(f"📈 RESOURCE UTILIZATION SUMMARY: {bag_name}")
    print("-" * 40)
    print(f"🔥 Peak CPU Usage:   {peak_cpu:8.2f} %")
    print(f"⚡ Avg CPU Usage:    {avg_cpu:8.2f} %")
    print(f"💾 Peak RAM Usage:   {peak_ram:8.2f} MB")
    print(f"📉 Final RAM Usage:  {final_ram:8.2f} MB")
    print("="*40 + "\n")

    # Generate Plot
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    ax1.plot(df['Time'], df['CPU'], 'g-', alpha=0.7, label='CPU Usage (%)')
    ax2.plot(df['Time'], df['RAM'], 'b-', linewidth=2, label='Memory Usage (MB)')
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('CPU (%)', color='g', fontweight='bold')
    ax2.set_ylabel('Memory (MB)', color='b', fontweight='bold')
    plt.title(f'FAST-LIO2 Resource Profile: {bag_name}')
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.savefig(results_dir / f"{bag_name}_resource_plot.png")
    print(f"🎉 Resource analysis complete. Files saved in {results_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 profile_fastlio.py [BAG_PATH] [CONFIG]")
    else:
        run_profile(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "avia.yaml")