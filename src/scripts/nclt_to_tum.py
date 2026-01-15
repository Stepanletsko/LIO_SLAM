import pandas as pd
import sys
import os

def convert_nclt_to_tum(input_file):
    # NCLT Ground Truth columns are usually: 
    # timestamp, x, y, z, roll, pitch, yaw
    # We need to convert this to TUM: timestamp x y z qx qy qz qw
    print(f"🔄 Converting {input_file}...")
    
    # Load NCLT CSV
    df = pd.read_csv(input_file)
    
    # NCLT stores time in microseconds. TUM needs seconds.
    df.iloc[:, 0] = df.iloc[:, 0] / 1e6
    
    # Since NCLT ground truth often lacks quaternions (it uses Euler), 
    # for a pure APE position check, we can fill orientation with 0,0,0,1 (identity)
    # evo_ape will primarily focus on the x, y, z translation for drift.
    
    tum_df = pd.DataFrame()
    tum_df['ts'] = df.iloc[:, 0]
    tum_df['x'] = df.iloc[:, 1]
    tum_df['y'] = df.iloc[:, 2]
    tum_df['z'] = df.iloc[:, 3]
    tum_df['qx'] = 0
    tum_df['qy'] = 0
    tum_df['qz'] = 0
    tum_df['qw'] = 1
    
    output_file = input_file.replace('.csv', '.tum')
    tum_df.to_csv(output_file, sep=' ', header=False, index=False)
    print(f"✅ Created: {output_file}")

if __name__ == "__main__":
    convert_nclt_to_tum(sys.argv[1])
