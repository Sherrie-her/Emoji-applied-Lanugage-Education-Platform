# Emoji-applied-Lanugage-Education-Platform

Project: Emo-Quiz (Emoji Learning Application)
Group 5

Members:
2019311148 Chaeri Son
2020314457 Daechan Yang
2019310146 Seungwoo Cho

## Installation Instructions

1. Database Set up
   - Install MySQL Workbench
   - Open MySQL Workbench and connect to your local server
   - Execute the following command to create and populate the database:
     mysql -u [username] -p < group5-db-dump.sql
   - Verify that the database 'rdbmsfinal' has been created successfully

2. Python Environment Set up
   - Ensure your Python version is 3.13.0
   - Create a virtual environment:
     python -m venv venv
   - Install required packages:
     pip install -r requirements.txt

3. Application Execution
   a. Download basic dataset:
      - emoji_description.csv
      - emoji_basic.csv
      - twemoji_final_png.zip (unzip it)
      - background.png
      - Font_BlackHanSans_Regular.ttf
   b. Create database & insert basic datasets:
      - Run ‘create_database_v4.sql’
      - Run ‘insert_basics.sql’ after setting file route
   c. Update the image directory path in group5-main.py:
      - Find all instances of "/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/"
      - Update route of background image too (bg=)
      - Replace with your local path to the project directory
   d. Run the main application:
      python group5-main.py

## Setup

1. Database Connection
   - Update the database credentials in the Database class if needed:
     host="localhost"
     user="root"
     password="20192024swa"
     database="rdbmsfinal"

2. Image Paths
   - Update all image paths for your local environment:
     Replace "/Users/choseungwoo/Desktop/" with your local path

## Project Structure

DB/
- Basic Data:
  - Leads to GUI-folder 1
- Data Preprocessing:
  - Database setting - leads to GUI-folder 2
  - Original Data:
    - emoji_df.csv: emoji-unicode table
    - emoji_map-original.csv: description in 15 languages
  - group5_data_cleaning.ipynb: Merging data tables with pandas
  - twemojidownload1.py: Download PNG files

GUI/
1. Download assets in <1. basic data to download (images, emoji data tables)>
2. Navigate to <2. database setting>:
   - Contains scripts for database creation and data insertion
   - Execute all queries after setting the file route
3. group5-main.py is the final application script

## Features

1. Study Mode
   - My Responses: View past responses
   - Story Mode: Create stories using emojis
   - Writing Mode: Practice describing emojis
   - Flashcard: Learn emoji meanings
2. Practice Mode
   - Multiple difficulty levels (Easy, Intermediate, Hard)
   - Game-based learning
   - Logs incorrect answers
3. Challenge Mode
   - Survival mode with time limits
   - High score updates
4. Profile
   - View rankings from Challenge Mode
   - Track incorrect answers

## Required Packages

- tkinter: Python 3.13.0
- tkinter.ttk: Python 3.13.0
- tkinter.messagebox: Python 3.13.0
- tkmacosx: 1.0.4
- Pillow (PIL fork): 9.2.0
- mysql-connector-python: 9.1.0
- random: Python 3.13.0
- os: Python 3.13.0
- json: Python 3.13.0
- datetime: Python 3.13.0

## Contact

For technical issues, please contact:
- Chaeri Son: bominnn3737@gmail.com
- Daechan Yang: ottery39@gmail.com
- Seungwoo Cho: seungwoo.sp@gmail.com
