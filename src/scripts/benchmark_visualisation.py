import matplotlib.pyplot as plt 

 

# Define the raw data 
# List of platform names (Intel first as baseline) 

platforms = [ 

'Intel Ultra 5 (Measured)', 

'Raspberry Pi 5', 

'Raspberry Pi 4B', 

'Jetson Orin Nano', 

'Jetson Nano', 

'Raspberry Pi 3B+' 

] 

# Corresponding Geekbench 6 single-core average scores 
# Higher score = faster performance 
scores = [2415, 899, 253, 691, 234, 98] 

# Measured baseline latency on Intel (in milliseconds) 
baseline_latency = 6.7 

# Baseline score (used as reference for scaling) 
baseline_score = scores[0] 

#Calculate projected latencies for all platforms 
latencies = [] 
platform_data = [] 

 

for i, (plat, score) in enumerate(zip(platforms, scores)): 

    if i == 0: 
        # For the baseline (Intel), use the real measured value 
        latency = baseline_latency 

    else: 

        # Basic projection: inverse scaling with benchmark score 
        # Higher score → lower (better) latency 
        projected = baseline_latency * (baseline_score / score) 

        # Apply 15% penalty for ARM platforms (RISC vs CISC difference) 
        adjusted = projected * 1 

        # Round to 1 decimal place
        latency = round(adjusted, 1) 

    # Store both name and calculated latency for later sorting 
    platform_data.append((plat, latency)) 
    latencies.append(latency) # temporary list, will be re-ordered later 


# Sort platforms: Intel first, then others from fastest → slowest === 
# Keep Intel always at position 0 
intel_entry = platform_data.pop(0) # Remove Intel from the list 


# Sort the remaining platforms by latency (ascending = fastest first) 
sorted_rest = sorted(platform_data, key=lambda x: x[1]) 
 

# Rebuild final ordered lists 
ordered_data = [intel_entry] + sorted_rest 

# Extract sorted names and latencies for plotting 
ordered_platforms = [item[0] for item in ordered_data] 
ordered_latencies = [item[1] for item in ordered_data] 

# Colors: green for Intel, red for Raspberry Pi family, blue for Jetson family 
colors = ['green' if 'Intel' in p else 'red' if 'Raspberry' in p else 'blue'  
for p in ordered_platforms] 

 

#  Create the plot
fig, ax = plt.subplots(figsize=(11, 6.5)) # Slightly wider to fit sorted labels nicely 

# Draw the bars using the ordered data 
ax.bar(ordered_platforms, ordered_latencies, color=colors, width=0.62) 

# Set axis labels and title 
ax.set_ylabel('Processing Time per Frame [ms]') 
ax.set_title('Normalised FAST-LIO2 Performance: Geekbench-Based Projections\n' ) 


# Add horizontal dashed red line for the real-time threshold (10 Hz = 100 ms) 
ax.axhline(y=100, color='red', linestyle='--', linewidth=1.4,  
label='Real-time Threshold (10Hz)') 

# Add exact latency value on top of every bar 
for i, latency in enumerate(ordered_latencies): 
    ax.text(i, latency + 3, f'{latency} ms',  
            ha='center', va='bottom', fontsize=10, fontweight='bold') 


# Rotate x-axis labels so they don't overlap 
plt.xticks(rotation=40, ha='right') 

# Add legend
plt.legend(loc='upper left') 
plt.tight_layout() 

# Show the plot on screen 
plt.show() 

#print the final ordered results for reference 
print("\nFinal ordered platforms (fastest → slowest after baseline):") 

for p, l in zip(ordered_platforms, ordered_latencies): 

    print(f"{p:25} → {l} ms") 