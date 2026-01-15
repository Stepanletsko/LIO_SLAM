import matplotlib.pyplot as plt

# Data constants from your specific run
total_instructions = 264232227444
total_frames = 1410
ipf = total_instructions / total_frames # ~187.4M
intel_measured_ms = 6.70

# Calculate projected times
plot_data = []
for name, data in architectures.items():
    if data["gips"] > 0:
        # Time (ms) = (Instructions / (GIPS * 10^9)) * 1000
        projected_ms = (ipf / (data["gips"] * 1e9)) * 1000
        plot_data.append((name, projected_ms, data["color"]))
    else:
        plot_data.append((name, data["time"], data["color"]))

# Sort data by time for a clean bar chart
plot_data.sort(key=lambda x: x[1])

names = [x[0] for x in plot_data]
times = [x[1] for x in plot_data]
colors = [x[2] for x in plot_data]

# Plotting
plt.figure(figsize=(12, 7))
bars = plt.bar(names, times, color=colors, edgecolor='black', alpha=0.8)

# Add real-time threshold line (10Hz = 100ms)
plt.axhline(y=100, color='red', linestyle='--', linewidth=2, label="Real-time Threshold (10Hz)")

# Styling
plt.ylabel('Processing Time per Frame (ms)', fontsize=12, fontweight='bold')
plt.title('Fast-LIO2 Performance: Measured vs. Architecture Projections\n(Workload: 187.4M Instructions/Frame)', fontsize=14, pad=20)
plt.xticks(rotation=15, ha='right')
plt.grid(axis='y', linestyle=':', alpha=0.6)

# Value labels on top of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.1f}ms', ha='center', fontweight='bold')

plt.legend()
plt.tight_layout()
plt.savefig('benchmark_comparison.png', dpi=300)
print("Graph saved as benchmark_comparison.png")
