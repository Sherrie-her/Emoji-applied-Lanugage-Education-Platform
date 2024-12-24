import pandas as pd
import requests
import os
from pathlib import Path

# File paths 
unicode_path = r"'/Users/(your name)/Downloads/Submission/DB/Data Preprocessing/Original Data/emoji_df.csv'" #please change this to your path
save_dir = r"C:\Users\user\OneDrive\Desktop\Emoji\twemoji_png"#please change this to your path  
failed_txt = r"C:\Users\user\OneDrive\Desktop\Emoji\failed_downloads.txt" #please change this to your path 
# Create the save directory if it doesn't exist
Path(save_dir).mkdir(parents=True, exist_ok=True)

# Read the Excel file
df = pd.read_excel(unicode_path)

failed_indices = []

# Process each emoji
for i, row in df.iterrows():
   index = row['index']
   code = str(row['codepoints']).lower()
   
   url = f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{code}.png"
   save_path = os.path.join(save_dir, f"twemoji_{index}.png")
   
   # Print progress every 50 emojis
   if index % 50 == 0:
       print(f"Processing emoji {index}...")
   
   try:
       response = requests.get(url)
       if response.status_code == 200:
           with open(save_path, 'wb') as f:
               f.write(response.content)
       else:
           failed_indices.append(index)
   
   except Exception as e:
       failed_indices.append(index)

# Save failed indices to a text file
if failed_indices:
   with open(failed_txt, 'w') as f:
       f.write('\n'.join(map(str, failed_indices)))
   print(f"\nFailed to download {len(failed_indices)} emojis.")
   print(f"The indices of failed downloads are saved in {failed_txt}.")
else:
   print("\nAll emojis were downloaded successfully!")

print("Download completed!")