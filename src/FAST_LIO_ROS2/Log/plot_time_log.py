import pandas as pd
import matplotlib.pyplot as plt
import sys

def plot_log(file_path):
    try:
        data = pd.read_csv(file_path)
        # Strip whitespace from headers
        data.columns = data.columns.str.strip()
    except Exception as e:
        print(f"Error: {e}")
        return

    # Extract Data (Convert seconds to ms)
    # 'math_time' is the old 'total time' (t5 - t0)
    # 'io_time' is the new column (t6 - t5)
    
    math_time = data['math_time'] * 1000.0
    io_time   = data['io_time'] * 1000.0
    total_time = math_time + io_time
    
    avg_io = io_time.mean()
    avg_math = math_time.mean()
    
    print(f"=== Performance Breakdown ===")
    print(f"Avg Math Time (Algorithm): {avg_math:.2f} ms")
    print(f"Avg I/O Time (Publishing): {avg_io:.2f} ms")
    print(f"TOTAL Time per Frame:      {(avg_math + avg_io):.2f} ms")
    
    # Plot Stacked Area Chart
    plt.figure(figsize=(12, 6))
    
    plt.stackplot(data.index, math_time, io_time, labels=['Math (Algorithm)', 'I/O (RAM/Publishing)'], colors=['#1f77b4', '#d62728'])
    
    # Draw the 100ms "Death Line" (10Hz limit)
    plt.axhline(y=100, color='k', linestyle='--', linewidth=2, label='10Hz Limit (100ms)')
    
    plt.xlabel('Frame Number')
    plt.ylabel('Time (ms)')
    plt.title('The Hidden Bottleneck: Math vs. I/O Time')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.show()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "src/FAST_LIO/Log/fast_lio_time_log.csv"
    plot_log(path)
