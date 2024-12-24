from tkinter import *
import tkinter as tk
from tkmacosx import *

import random
from tkinter import ttk, messagebox
from PIL import ImageTk, Image

import mysql.connector

import os
import json
from datetime import datetime

# Class for Database Selection
class Database: 
    _instance = None
    _connection = None
    _cursor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        """Establish database connection"""
        if not self._connection:
            try:
                self._connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="20192024swa", 
                    database="rdbmsfinal"
                )
                self._cursor = self._connection.cursor(dictionary=True)
            except mysql.connector.Error as err:
                print(f"Error connecting to database: {err}")
                raise

    @property
    def connection(self):
        """Get database connection"""
        if not self._connection or not self._connection.is_connected():
            self._connect()
        return self._connection

    @property
    def cursor(self):
        """Get database cursor"""
        if not self._cursor or not self._connection.is_connected():
            self._connect()
        return self._cursor

    def commit(self):
        """Commit transaction"""
        self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        self.connection.rollback()

    def close(self):
        """Close database connection"""
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()
            self._connection = None
            self._cursor = None

root = Tk()
root.title("Emo-Quiz")
root.geometry("800x600")
root.resizable(0,0)

current_screen = ""
current_nickname = ""
current_user_id = ""

game_frame = None
game_instance = None

language_option = StringVar()

# Create a Dictionary to store font style
FONT_STYLES = {
    'tiny': ('Black Han Sans', 8, 'normal'),
    'small': ('Black Han Sans', 10, 'normal'),
    'label': ('Black Han Sans', 12, 'normal'),
    'button': ('Black Han Sans', 14, 'bold'),
    'entry': ('Black Han Sans', 16, 'normal'),
    'message': ('Black Han Sans', 20, 'normal'),
    'title': ('Hanalei Fill', 40, 'bold'),
}

# Classes
class PracticeModeStart:
    def __init__(self, root, user_id=1, language='kor', difficulty='easy', category='All categories'):
        self.root = root
        
        self.user_id = user_id
        self.language = language
        self.difficulty = difficulty
        self.category = category
            
        self.available_languages = ['deu', 'zho', 'kor', 'eng', 'zho', 'spa', 'fra', 'jpn', 'por', 'ita', 'fas', 'ind', 'rus', 'ary', 'arb']
        self.options_count = {'easy': 4,'intermediate': 6,'hard': 8}
        self.current_options = self.options_count[difficulty]
        
        
        
        self.db = Database()
        self.cursor = self.db.cursor

        self.current_round = 1
        self.total_rounds = 10
        self.image_dir = r"/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/twemoji_final_png"
        self.correct_answers = 0
        self.correct_idx = None
        
        self.generate_questions()
        self.setup_ui()
        self.start_new_round()

    def generate_questions(self):
        self.cursor.execute("DELETE FROM practice_log")
        self.db.commit()
        
        for _ in range(self.total_rounds):
            query_correct = f"""
            SELECT eb.idx, ed.description_{self.language} as description
            FROM rdbmsfinal.emoji_basic eb
            JOIN rdbmsfinal.emoji_description ed ON eb.idx = ed.idx
            WHERE ed.description_{self.language} IS NOT NULL
            ORDER BY RAND()
            LIMIT 1
            """
            self.cursor.execute(query_correct)
            correct = self.cursor.fetchone()
            
            wrong_count = self.current_options - 1
            query_wrong = f"""
            SELECT eb.idx
            FROM rdbmsfinal.emoji_basic eb
            JOIN rdbmsfinal.emoji_description ed ON eb.idx = ed.idx
            WHERE eb.idx != {correct['idx']}
            AND ed.description_{self.language} IS NOT NULL
            ORDER BY RAND()
            LIMIT {wrong_count}
            """
            self.cursor.execute(query_wrong)
            wrong = self.cursor.fetchall()
            wrong_ids = [str(w['idx']) for w in wrong]
            
            insert_query = """
            INSERT INTO practice_log 
            (correct_idx, wrong_idx, correct, correct_description, difficulty)
            VALUES (%s, %s, FALSE, %s, %s)
            """
            self.cursor.execute(insert_query, 
                (correct['idx'], json.dumps(wrong_ids), correct['description'], self.difficulty))
            self.db.commit()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('default')

        # progress bar
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#E0E0E0',     
            background='#4CAF50',      
            lightcolor='#4CAF50',      
            darkcolor='#4CAF50'        
        )
        self.progress = ttk.Progressbar(
            self.root,
            orient='horizontal',
            length=630,
            mode='determinate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=9)

        self.description_label = Label(
            self.root,
            text="",
            font=FONT_STYLES['button'],
            fg="black",
            bg="#FFFCEE",
            wraplength=630
        )
        self.description_label.pack(pady=13)

        self.button_frame = Frame(
            self.root,
            bg="#FFFCEE",)
        self.button_frame.pack(pady=18)
        
        grid_layouts = {
            'easy': (2, 2),
            'intermediate': (2, 3),
            'hard': (2, 4)
        }
        rows, cols = grid_layouts[self.difficulty]
        
        self.buttons = []
        for i in range(rows):
            for j in range(cols):
                btn = Button(
                    self.button_frame,
                    width=135,
                    height=135,
                    command=lambda x=i, y=j: self.button_click(x, y)
                )
                btn.grid(row=i, column=j, padx=4, pady=4)
                self.buttons.append(btn)

        self.score_label = Label(
            self.root,
            text=f"Score: {self.correct_answers}/0",
            font=FONT_STYLES['label'],
            fg="black",
            bg="#FFFCEE"
        )
        self.score_label.pack(pady=4)

    def start_new_round(self):
        query = f"""
        SELECT *
        FROM practice_log
        LIMIT {self.current_round-1}, 1
        """
        self.cursor.execute(query)
        question = self.cursor.fetchone()
        
        self.correct_idx = question['correct_idx']
        wrong_idx_list = json.loads(question['wrong_idx'])
        
        self.description_label.config(text=question['correct_description'])
        
        all_idx = [str(self.correct_idx)] + wrong_idx_list
        random.shuffle(all_idx)
        
        self.images = []
        for i, idx in enumerate(all_idx):
            image_filename = f"twemoji_{idx}.png"
            image_path = os.path.join(self.image_dir, image_filename)
            
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image = image.resize((126, 126), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.images.append(photo)
                self.buttons[i].config(image=photo)
                self.buttons[i].idx = int(idx)
        
        self.score_label.config(text=f"Score: {self.correct_answers}/{self.current_round-1}")
        progress_value = ((self.current_round - 1) / self.total_rounds) * 100
        self.progress.configure(value=progress_value)

    def button_click(self, x, y):
        cols = {
            'easy': 2,
            'intermediate': 3,
            'hard': 4
        }[self.difficulty]
        
        button_idx = x * cols + y
        clicked_button = self.buttons[button_idx]
        
        if hasattr(clicked_button, 'idx') and clicked_button.idx == self.correct_idx:
            self.correct_answers += 1
            
            update_query = """
            UPDATE practice_log 
            SET correct = TRUE 
            WHERE correct_idx = %s
            """
            self.cursor.execute(update_query, (self.correct_idx,))
            self.db.commit()
        
        if self.current_round < self.total_rounds:
            self.current_round += 1
            self.start_new_round()
        else:
            self.show_results()

    def show_results(self):
        # Clear current UI
        for widget in self.root.winfo_children():
            widget.destroy()

        # Show final score
        tk.Label(
            self.root,
            text="Practice mode finished!",
            font=FONT_STYLES['entry'],
            fg='#4CAF50',
            bg="#FFFCEE"
        ).pack(pady=5)
        
        tk.Label(
            self.root,
            text=f"Final score: {self.correct_answers}/{self.total_rounds}",
            font=FONT_STYLES['entry'],
            fg="black",
            bg="#FFFCEE"
        ).pack(pady=10)

        # Get wrong questions
        query = f"""
        SELECT p.correct_idx, 
            p.correct_description as game_description,
            ed.description_eng as eng_description
        FROM practice_log p
        JOIN rdbmsfinal.emoji_description ed ON p.correct_idx = ed.idx
        WHERE p.correct = FALSE
        """
        self.cursor.execute(query)
        wrong_questions = self.cursor.fetchall()

        if wrong_questions:
            # Save wrong answers
            try:
                self.cursor.execute("START TRANSACTION")
                
                # Delete existing wrong answers
                delete_game_log = """
                DELETE FROM game_log 
                WHERE user_id = %s 
                AND correct_idx IN (SELECT correct_idx FROM practice_log)
                """
                self.cursor.execute(delete_game_log, (self.user_id,))
                
                # Insert new wrong answers
                for wrong in wrong_questions:
                    insert_query = """
                    INSERT INTO game_log 
                    (user_id, game_language, difficulty, correct_idx)
                    VALUES (%s, %s, %s, %s)
                    """
                    self.cursor.execute(insert_query, (
                        self.user_id,
                        self.language,
                        self.difficulty,
                        wrong['correct_idx']
                    ))
                
                self.cursor.execute("DELETE FROM practice_log")
                self.db.commit()
                
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                self.db.rollback()

            # Show wrong answers
            tk.Label(
                self.root,
                text="\nWrong answers:",
                font=FONT_STYLES['button'],
                fg="black",
                bg="#FFFCEE"
            ).pack(pady=10)
            
            # Create scrollable frame
            frame = tk.Frame(
                self.root,
                bg='#FFF5D1'
            )
            frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            canvas = tk.Canvas(
                frame,
                bg='#FFF5D1'
            )
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(
                canvas,
                bg='#FFF5D1')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Show each wrong answer
            for i, wrong in enumerate(wrong_questions, 1):
                question_frame = tk.Frame(
                    scrollable_frame,
                    bg='#FFF5D1')
                question_frame.pack(fill='x', pady=10)
                
                # Show emoji image
                image_path = os.path.join(
                    self.image_dir,
                    f"twemoji_{wrong['correct_idx']}.png"
                )
                
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    image = image.resize((50, 50), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    image_label = tk.Label(
                        question_frame,
                        image=photo,
                        bg='#FFF5D1')
                    image_label.image = photo
                    image_label.pack(side='left', padx=5)
                
                # Show descriptions
                text_frame = tk.Frame(
                    question_frame,
                    bg='#FFF5D1')
                text_frame.pack(side='left', fill='x', expand=True)
                
                tk.Label(
                    text_frame,
                    text=f"{i}. {wrong['eng_description']}",
                    font=FONT_STYLES['small'],
                    bg='#FFF5D1',
                    wraplength=500,
                    justify=tk.LEFT
                ).pack(anchor='w')
                
                if self.language != 'eng':
                    tk.Label(
                        text_frame,
                        text=f"    {wrong['game_description']}",
                        font=FONT_STYLES['small'],
                        wraplength=500,
                        justify=tk.LEFT,
                        fg='#666666',
                        bg='#FFF5D1'
                    ).pack(anchor='w')
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        self.cursor.close()
        self.db.close()
class SurvivalModeStart:
    def __init__(self, root, user_id=1, language='kor'):
        self.root = root

        self.user_id = user_id
        self.language = language
        self.game_running = True

        # basic setting
        self.image_dir = r"/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/twemoji_final_png"
        self.correct_answers = 0
        self.correct_idx = None
        self.time_remaining = 5000  # 5seconds in ms
        
        # DB connection
        self.db = Database()
        self.cursor = self.db.cursor
        
        self.setup_ui()
        
        self.start_new_round()
        
        self.update_timer()


    def setup_ui(self):
        # Progress bar (timer)
        self.progress = ttk.Progressbar(
            self.root,
            orient='horizontal',
            length=700,
            mode='determinate',
            maximum=5000  
        )
        self.progress.pack(pady=10)
        
        # Description
        self.description_label = tk.Label(
            self.root,
            text="",
            font=FONT_STYLES['entry'],
            fg="black",
            bg="#FFFCEE",
            wraplength=700
        )
        self.description_label.pack(pady=15)
        

        self.create_button_grid()
        
        # Pass button
        self.pass_button = tk.Button(
            self.root,
            text="pass",
            command=self.game_over,
            font=FONT_STYLES['label']
        )
        self.pass_button.pack(pady=10)
        
        # Score
        self.score_label = tk.Label(
            self.root,
            text=f"Score: {self.correct_answers}",
            font=FONT_STYLES['button']
        )
        self.score_label.pack(pady=5)

    def create_button_grid(self):
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=20)
        
        # 2x4 grid for buttons
        self.buttons = []
        for i in range(2):
            for j in range(4):
                btn = tk.Button(
                    self.button_frame,
                    width=150,
                    height=150,
                    command=lambda x=i, y=j: self.button_click(x, y)
                )
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.buttons.append(btn)

    def update_timer(self):
        if self.game_running and self.time_remaining > 0:  
            self.time_remaining -= 100
            self.progress['value'] = self.time_remaining
            self.root.after(100, self.update_timer)
        elif self.game_running:  # timeover
            self.game_over()

    def get_new_question(self):
        query = """
        SELECT eb.idx, ed.description_{} as description
        FROM rdbmsfinal.emoji_basic eb
        JOIN rdbmsfinal.emoji_description ed ON eb.idx = ed.idx
        WHERE ed.description_{} IS NOT NULL
        ORDER BY RAND()
        LIMIT 1
        """.format(self.language, self.language)
        
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def get_wrong_options(self, correct_idx):
        query = """
        SELECT eb.idx
        FROM rdbmsfinal.emoji_basic eb
        JOIN rdbmsfinal.emoji_description ed ON eb.idx = ed.idx
        WHERE eb.idx != {}
        AND ed.description_{} IS NOT NULL
        ORDER BY RAND()
        LIMIT 7
        """.format(correct_idx, self.language)
        
        self.cursor.execute(query)
        wrong = self.cursor.fetchall()
        return [str(w['idx']) for w in wrong]

    def start_new_round(self):
        # bringing new question
        correct = self.get_new_question()
        wrong_options = self.get_wrong_options(correct['idx'])
        
        # UI update
        self.correct_idx = correct['idx']
        self.description_label.config(text=correct['description'])
        
        options = [str(self.correct_idx)] + wrong_options
        random.shuffle(options)
        self.update_buttons(options)
        
        # timer reset
        self.time_remaining = 5000
        self.progress['value'] = 5000

    def update_buttons(self, options):
        self.images = []
        for i, idx in enumerate(options):
            image_filename = f"twemoji_{idx}.png"
            image_path = os.path.join(self.image_dir, image_filename)
            
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image = image.resize((140, 140), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.images.append(photo)
                self.buttons[i].config(image=photo)
                self.buttons[i].idx = int(idx)

    def button_click(self, x, y):
        button_idx = x * 4 + y  # button number
        clicked_button = self.buttons[button_idx]
        
        if hasattr(clicked_button, 'idx') and clicked_button.idx == self.correct_idx:
            self.correct_answers += 1
            self.score_label.config(text=f"Score: {self.correct_answers}")
            self.start_new_round()
        else:
            self.game_over()

    def update_best_score(self):
        # bringing previous bestscore
        select_query = """
        SELECT best_score
        FROM user
        WHERE user_id = %s
        """
        self.cursor.execute(select_query, (self.user_id,))
        result = self.cursor.fetchone()
        
        try:
            if result['best_score'] is None:
                current_scores = {}
            else:
                try:
                    # JSOn type parsing
                    current_scores = json.loads(result['best_score'])
                except (TypeError, json.JSONDecodeError):
                    current_scores = {}
        
            # update highscore
            if self.correct_answers > current_scores.get(self.language, 0):
                current_scores[self.language] = self.correct_answers
                update_query = """
                UPDATE user 
                SET best_score = %s
                WHERE user_id = %s
                """
                self.cursor.execute(update_query, (
                    json.dumps(current_scores),
                    self.user_id
                ))
                self.db.commit()
                
        except mysql.connector.Error as err:
            print(f"Error updating best score: {err}")
            self.db.rollback()

    def game_over(self):
        self.game_running = False
        
        try:
            select_query = """
            SELECT best_score
            FROM user
            WHERE user_id = %s
            """
            self.cursor.execute(select_query, (self.user_id,))
            result = self.cursor.fetchone()
            
            previous_score = 0
            if result['best_score'] is not None:
                try:
                    scores = json.loads(result['best_score'])
                    if isinstance(scores, dict):
                        previous_score = scores.get(self.language, 0)
                except (TypeError, json.JSONDecodeError):
                    try:
                        previous_score = int(result['best_score'])
                    except (TypeError, ValueError):
                        previous_score = 0

            if self.correct_answers > previous_score:
                scores = {self.language: self.correct_answers}
                update_query = """
                UPDATE user 
                SET best_score = %s
                WHERE user_id = %s
                """
                self.cursor.execute(update_query, (
                    json.dumps(scores),
                    self.user_id
                ))
                self.db.commit()

            for widget in self.root.winfo_children():
                widget.destroy()
            
            # game over frame
            game_over_frame = tk.Frame(
                self.root,
                bg="#FFFCEE")
            game_over_frame.pack(expand=True)
            
            tk.Label(
                game_over_frame,
                text="Game Over!",
                font=FONT_STYLES['title'],
                fg="#FF626C",
                bg="#FFFCEE"
            ).pack(pady=20)
            
            # final score
            tk.Label(
                game_over_frame,
                text=f"Final Score: {self.correct_answers}",
                font=FONT_STYLES['message'],
                fg="black",
                bg="#FFFCEE"
            ).pack(pady=10)
            
            # highscore message
            if self.correct_answers > previous_score:
                self.update_best_score()
                tk.Label(
                    game_over_frame,
                    text="New High Score!",
                    font=FONT_STYLES['entry'],
                    fg='#4CAF50',  
                    bg="#FFFCEE"
                ).pack(pady=10)
            else:
                tk.Label(
                    game_over_frame,
                    text=f"Previous highscore: {previous_score}",
                    font=FONT_STYLES['entry'],
                    fg="black",
                    bg="#FFFCEE"
                ).pack(pady=10)
        finally:
            self.cursor.close()
            self.db.close()

class ResponseViewer:
    def __init__(self, root, user_id):
        self.root = root
        self.user_id = user_id
        
        self.db = Database()
        self.cursor = self.db.cursor
        self.group_by = "none"

        self.main_frame = Frame(
            self.root,
            bg="#FFFCEE"
        )
        self.main_frame.place(x=0, rely=0.1, relwidth=1, relheight=0.9)
        
        self.title_label = Label(
            self.main_frame,
            text="My Responses",
            font=FONT_STYLES['message'],
            fg='black',
            bg="#FFFCEE",
            pady=20
        )
        self.title_label.pack()

        self.filter_frame = Frame(
            self.main_frame,
            bg="#FFFCEE"
        )
        self.filter_frame.pack(pady=20)
        
        # Tree Frame view that can see the responses
        self.tree_frame = Frame(
            self.main_frame,
            bg='#FFF5D1'
        )
        self.tree_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.create_widgets()
        self.load_responses()

    def create_widgets(self):
        Label(
            self.filter_frame,
            text="Group By:",
            font=FONT_STYLES['label'],
            fg='black',
            bg="#FFFCEE"
        ).pack(side='left', padx=5)
        
        # Filter Buttons
        self.none_btn = Button(
            self.filter_frame,
            text="None",
            command=lambda: self.change_group_by("none"),
            font=FONT_STYLES['small'],
            bg="#61F9B3",
            relief="sunken"
        )
        self.none_btn.pack(side='left', padx=5)

        self.mode_btn = Button(
            self.filter_frame,
            text="Mode",
            command=lambda: self.change_group_by("mode"),
            font=FONT_STYLES['small'],
            fg='black',
            bg="#61F9B3"
        )
        self.mode_btn.pack(side='left', padx=5)

        self.lang_btn = Button(
            self.filter_frame,
            text="Language",
            command=lambda: self.change_group_by("language"),
            font=FONT_STYLES['small'],
            bg="#61F9B3"
        )
        self.lang_btn.pack(side='left', padx=5)

        style = ttk.Style()
        style.configure(
            "Treeview",
            font=FONT_STYLES['tiny'],  
            rowheight=30  
        )
        style.configure(
            "Treeview.Heading",
            font=FONT_STYLES['small']  
        )
        
        tree_container = Frame(self.tree_frame)
        tree_container.pack(fill='both', expand=True)

        columns = ("Date", "Language", "Mode", "Response")
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            height=15
        )

        for col in columns:
            self.tree.heading(col, text=col)

        self.tree.column("Date", width=100)
        self.tree.column("Language", width=75)
        self.tree.column("Mode", width=75)
        self.tree.column("Response", width=550)
        
        y_scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.tree.yview
        )
        x_scrollbar = ttk.Scrollbar(
            tree_container,
            orient="horizontal",
            command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

    def change_group_by(self, group_type):
        # Update button states
        self.none_btn.config(relief="raised")
        self.mode_btn.config(relief="raised")
        self.lang_btn.config(relief="raised")
        
        if group_type == "none":
            self.none_btn.config(relief="sunken")
        elif group_type == "mode":
            self.mode_btn.config(relief="sunken")
        elif group_type == "language":
            self.lang_btn.config(relief="sunken")
        
        self.group_by = group_type
        self.load_responses()

    def load_responses(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Different queries based on grouping, excluding survival mode
        if self.group_by == "none":
            query = """
            SELECT 
                DATE_FORMAT(date, '%Y.%m.%d') as date,
                language,
                mode,
                response
            FROM my_responses
            WHERE mode != 'survival'
            AND user_id = %s
            ORDER BY date DESC, language ASC
            """
        elif self.group_by == "mode":
            query = """
            SELECT 
                DATE_FORMAT(date, '%Y.%m.%d') as date,
                language,
                mode,
                GROUP_CONCAT(response SEPARATOR ', ') as response
            FROM my_responses
            WHERE mode != 'survival'
            AND user_id = %s
            GROUP BY mode, date, language
            ORDER BY mode ASC
            """
        else:  # language
            query = """
            SELECT 
                DATE_FORMAT(date, '%Y.%m.%d') as date,
                language,
                mode,
                GROUP_CONCAT(response SEPARATOR ', ') as response
            FROM my_responses
            WHERE mode != 'survival'
            AND user_id = %s
            GROUP BY language, date, mode
            ORDER BY language ASC
            """
            
        self.cursor.execute(query, (self.user_id,))
        responses = self.cursor.fetchall()
        
        for response in responses:
            self.tree.insert("", "end", values=(
                response['date'],
                response['language'],
                response['mode'],
                response['response']
            ))
class FlashcardModeStart:
    def __init__(self, root):
        self.root = root
        
        # Configure theme
        self.root.configure(bg='#1e1e1e')
        self.style = ttk.Style()
        # Dictionary mapping language names to their ISO codes
        self.languages = {
            'English': 'eng', 'German': 'deu', 'Spanish': 'spa', 'French': 'fra',
            'Japanese': 'jpn', 'Korean': 'kor','Portuguese': 'por', 'Italian': 'ita',
            'Persian (Farsi)': 'fas', 'Indonesian': 'ind', 'Chinese': 'zho',
            'Russian': 'rus', 'Turkish': 'tur', 'Moroccan Arabic': 'ary', 'Arabic': 'arb'
        }
        
        self.db = Database()
        self.cursor = self.db.cursor
        
        # Initialize variables
        self.current_cards = []
        self.card_index = 0
        self.image_dir = r"/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/twemoji_final_png"
        
        self.current_language = 'eng'  # Default language is English
        
        global language_option
        self.current_language = self.languages.get(language_option.get(), 'eng')

        self.setup_ui()
        self.load_all_emojis()
        
    def setup_ui(self):
        # Configure UI theme and styles
        style = ttk.Style()
        style.theme_use('default')
        
        # Set main background color
        self.root.configure(bg="#FFFCEE")
        
        # Configure notebook styles for tabs
        style.configure(
            "Custom.TNotebook", 
            background="#FFFCEE",
            borderwidth=0
        )
        style.configure(
            "Custom.TNotebook.Tab",
            background="#FFFCEE",
            borderwidth=1,
            font=FONT_STYLES['button']
        )
        
        # Create main notebook for tab navigation
        self.notebook = ttk.Notebook(
            self.root,
            style="Custom.TNotebook"
        )
        self.notebook.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)
        
        # Create main frames for different modes
        self.select_set_frame = Frame(
            self.notebook,
            bg="#FFFCEE"
        )
        self.learn_frame = Frame(
            self.notebook,
            bg="#FFFCEE"
        )
        
        self.notebook.add(self.select_set_frame, text='Select Set')
        self.notebook.add(self.learn_frame, text='Learn Mode')
        
        self.setup_select_tab()
        self.setup_learn_mode()
        
    def setup_select_tab(self):
    # Language selection UI components
        Label(
            self.select_set_frame,
            text="Select Language:",
            font=FONT_STYLES['label'],
            fg="black",
            bg="#FFFCEE"
        ).pack(pady=10)
        
        self.language_var = StringVar(value='English')
        language_frame = Frame(
            self.select_set_frame,
            bg="#FFFCEE"
        )
        language_frame.pack(pady=10)
        
        # Language dropdown menu
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=list(self.languages.keys()),
            state='readonly',
            font=FONT_STYLES['label'],
            width=20
        )
        language_combo.pack()
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)

        # Category selection UI components
        Label(
            self.select_set_frame,
            text="Select Category:",
            font=FONT_STYLES['label'],
            fg="black",
            bg="#FFFCEE"
        ).pack(pady=20)
        
        category_frame = Frame(
            self.select_set_frame,
            bg="#FFFCEE"
        )
        category_frame.pack(pady=10)
        
        # Category dropdown menu
        self.category_var = StringVar(value="Food & Drink")
        self.category_combo = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            state='readonly',
            font=FONT_STYLES['label'],
            width=20
        )
        self.category_combo.pack()
        
        # Load categories from database
        self.cursor.execute("SELECT DISTINCT category FROM emoji_basic")
        categories = [row['category'] for row in self.cursor.fetchall()]
        self.category_combo['values'] = categories
        
        # Start learning button
        Button(
            self.select_set_frame,
            text="Start Learning",
            command=self.load_category_emojis,
            font=FONT_STYLES['button'],
            bg="#FFD700",
            fg="black",
            width=200,
            height=50
        ).pack(pady=30)
        
    def on_language_change(self, event=None):
        # Update current language when selection changes
        self.current_language = self.languages[self.language_var.get()]
        
    def setup_learn_mode(self):
        # Setup learning interface
        main_container = Frame(
            self.learn_frame,
            bg="#FFFCEE")
        main_container.pack(expand=True, fill='both')
        
        # Word/description display label
        self.word_label = Label(
            main_container,
            text="",
            font=FONT_STYLES['message'],
            fg="black",
            bg="#FFFCEE"
        )
        self.word_label.pack(pady=20)
        
        # Emoji image display label
        self.emoji_label = Label(
            main_container,
            bg="#FFFCEE"
        )
        self.emoji_label.pack(pady=10)
        
        # Navigation buttons container
        button_container = Frame(
            main_container,
            bg="#FFFCEE"
        )
        button_container.pack(side='bottom', pady=80)
        
        # Button styles
        button_style = {
            'bg': "#FFD700",
            'fg': "black",
            'font': FONT_STYLES['button'],
            'width': 120,
            'height': 50
        }
        button_style_flip = {
            'bg': "#45CF8F",
            'fg': "black",
            'font': FONT_STYLES['button'],
            'width': 120,
            'height': 50
        }

        # Navigation buttons
        self.prev_btn = Button(
            button_container,
            text="Previous",
            command=self.prev_card,
            **button_style
        )
        self.prev_btn.pack(side='left', padx=5)
        
        self.flip_btn = Button(
            button_container,
            text="Flip", 
            command=self.flip_card,
            **button_style_flip
        )
        self.flip_btn.pack(side='left', padx=5)
        
        self.next_btn = Button(
            button_container,
            text="Next",
            command=self.next_card,
            **button_style
        )
        self.next_btn.pack(side='left', padx=5)

    def load_all_emojis(self):
        # Load all emoji cards from database with their descriptions
        self.cursor.execute(f"""
        SELECT eb.idx, eb.emoji, eb.category, 
               ed.description_{self.current_language} as description_eng
        FROM emoji_basic eb
        JOIN emoji_description ed ON eb.idx = ed.idx
        """)

        self.current_cards = self.cursor.fetchall()
        if self.current_cards:
            self.show_card()

    def load_category_emojis(self):
        # Load emoji cards filtered by selected category
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Warning", "Please select a category first")
            return
            
        self.cursor.execute(f"""
        SELECT eb.idx, eb.emoji, eb.category, 
               ed.description_{self.current_language} as description_eng
        FROM emoji_basic eb
        JOIN emoji_description ed ON eb.idx = ed.idx
        WHERE eb.category = %s
    """, (category,))
        
        self.current_cards = self.cursor.fetchall()
        self.card_index = 0
        
        if self.current_cards:
            self.notebook.select(1)  # Switch to Learn Mode tab
            self.show_card()
        else:
            messagebox.showinfo("Info", "No emoji cards found in this category")

    def load_emoji(self, idx):
        # Load and resize emoji image from file
        try:
            image_path = os.path.join(self.image_dir, f"twemoji_{idx}.png")
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image = image.resize((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                return photo
            else:
                print(f"Image not found: {image_path}")
                return None
        except Exception as e:
            print(f"Error loading emoji: {e}")
            return None
    
    def show_card(self):
        # Display current card's emoji and index
        if not self.current_cards:
            self.word_label.config(text="No cards to display")
            self.emoji_label.config(image='')
            return
        
        card = self.current_cards[self.card_index]
        total_cards = len(self.current_cards)
        current_num = self.card_index + 1
        self.word_label.config(text=f"{current_num}/{total_cards}")
        
        emoji_image = self.load_emoji(card['idx'])
        if emoji_image:
            self.emoji_label.config(image=emoji_image)
            self.emoji_label.image = emoji_image
        else:
            self.emoji_label.config(image='')

    def flip_card(self):
        # Toggle between showing emoji and description
        if not self.current_cards:
            return
            
        card = self.current_cards[self.card_index]
        total_cards = len(self.current_cards)
        current_num = self.card_index + 1
        current_text = self.word_label.cget('text')
        
        if current_text == f"{current_num}/{total_cards}":
            self.word_label.config(text=card['description_eng'])
            self.emoji_label.config(image='')
        else:
            self.word_label.config(text=f"{current_num}/{total_cards}")
            emoji_image = self.load_emoji(card['idx'])
            if emoji_image:
                self.emoji_label.config(image=emoji_image)
                self.emoji_label.image = emoji_image

    def next_card(self):
        # Move to next card with wraparound
        if self.current_cards:
            self.card_index = (self.card_index + 1) % len(self.current_cards)
            self.show_card()

    def prev_card(self):
        # Move to previous card with wraparound
        if self.current_cards:
            self.card_index = (self.card_index - 1) % len(self.current_cards)
            self.show_card()
class ResponseTracker:
    """
    Tracking the responses from story mode and writing mode
    Get current date for logging at the end 
    """
    def __init__(self, db_connection):
        # Initialize database connection and cursor
        self.db = db_connection
        self.cursor = self.db.cursor
    
    def log_response(self, user_id, language, mode, response):
        # SQL query to insert user response data into my_responses table
        insert_query = """
        INSERT INTO my_responses 
        (user_id, date, language, mode, response) 
        VALUES (%s, %s, %s, %s, %s)
        """
        # Get current date for logging
        current_date = datetime.now().date()
        
        # Execute insert query with provided parameters
        self.cursor.execute(
            insert_query, 
            (user_id, current_date, language, mode, response)
        )
        # Commit the transaction to save changes
        self.db.commit()
class StoryModeStart:
    def __init__(self, root, user_id, language):
        self.root = root
        self.user_id = user_id
        
        # Language mapping dictionary for supporting multiple languages
        self.languages = {
            'English': 'eng', 'German': 'deu', 'Spanish': 'spa', 'French': 'fra',
            'Japanese': 'jpn', 'Korean': 'kor', 'Portuguese': 'por', 'Italian': 'ita',
            'Persian': 'fas', 'Indonesian': 'ind', 'Chinese': 'zho', 'Russian': 'rus',
            'Turkish': 'tur', 'Moroccan Arabic': 'ary', 'Arabic': 'arb'
        }
        
        self.db = Database()
        self.cursor = self.db.cursor
        
        # Initialize response tracker for logging user responses
        self.response_tracker = ResponseTracker(self.db)
        
        # Game state initialization
        self.current_round = 1
        self.total_rounds = 10
        self.image_dir = r"/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/twemoji_final_png"
        self.current_emojis = []
        self.current_language = language
        
        # Setup UI components
        self.setup_ui()
        
        # Start first round of the game
        self.start_new_round()

    def setup_ui(self):
        # Main container with light background
        container = Frame(
            self.root,
            bg='#FFFCEE',
            padx=20
        )
        container.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        # Progress bar for tracking game progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            container,
            orient='horizontal',
            length=760,
            maximum=self.total_rounds,
            variable=self.progress_var,
            mode='determinate',
            style="Pink.Horizontal.TProgressbar"
        )
        self.progress_bar.place(relx=0, rely=0.05)

        # Frame for displaying emoji images
        self.emoji_frame = Frame(
            container,
            bg='#FFFCEE'
        )
        self.emoji_frame.place(relx=0.5, rely=0.2, anchor='center')

        # Text input area for user stories
        self.text_input = Text(
            container,
            height=8,
            width=40,
            font=('pretendard', 14, 'bold'),
            relief="solid",
            bd=1,
            fg='black',
            bg='#F4D2FF'
        )
        self.text_input.place(relx=0.5, rely=0.55, anchor='center')
        
        # Set default text and bind focus events
        self.text_input.insert('1.0', "Make your story with Emojis")
        self.text_input.config(fg='#F4D2FF')
        self.text_input.bind('<FocusIn>', self.on_entry_click)
        self.text_input.bind('<FocusOut>', self.on_focus_out)

        # Button container
        button_frame = Frame(
            container,
            bg='#FFFCEE'
        )
        button_frame.place(relx=0.5, rely=0.85, anchor='center')

        # Submit and Pass buttons
        self.submit_button = Button(
            button_frame,
            text="Submit",
            command=self.check_answer,
            font=FONT_STYLES['label'],
            bg="#45CF8F",
            width=100
        )
        self.submit_button.pack(side='left', padx=5)

        self.pass_button = Button(
            button_frame,
            text="Pass",
            command=self.next_question,
            font=FONT_STYLES['label'],
            bg="#FFD700",
            width=100
        )
        self.pass_button.pack(side='left', padx=5)

    def change_language(self):
        # Update current language based on selection
        selected_language = self.language_var.get()
        self.current_language = self.languages[selected_language]

    def on_entry_click(self, event):
        # Clear placeholder text when input is focused
        if self.text_input.get('1.0', 'end-1c') == "Please type it....":
            self.text_input.delete('1.0', tk.END)
            self.text_input.config(fg='black')

    def on_focus_out(self, event):
        # Restore placeholder text if input is empty
        if self.text_input.get('1.0', 'end-1c') == '':
            self.text_input.insert('1.0', "Please type it....")
            self.text_input.config(fg='grey')

    def start_new_round(self):
        # Clear previous emoji displays
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()

        # Select random emojis from database
        query = """
        SELECT idx FROM emoji_basic
        ORDER BY RAND()
        LIMIT 5
        """
        self.cursor.execute(query)
        self.current_emojis = self.cursor.fetchall()

        # Display selected emoji images
        for emoji in self.current_emojis:
            image_filename = f"twemoji_{emoji['idx']}.png"
            image_path = os.path.join(self.image_dir, image_filename)
            
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image = image.resize((70, 70), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                emoji_label = Label(
                    self.emoji_frame,
                    image=photo,
                    bg='#FFFCEE'
                )
                emoji_label.image = photo
                emoji_label.pack(side='left', padx=5)

        # Reset text input to default state
        self.text_input.delete('1.0', tk.END)
        self.text_input.insert('1.0', "Please type it....")
        self.text_input.config(fg='grey')
        
        # Update progress bar
        self.progress_var.set(self.current_round - 1)

    def check_answer(self):
        # Log user's story response
        user_response = self.text_input.get('1.0', 'end-1c').strip()
        if user_response and user_response != "Please type it....":
            self.response_tracker.log_response(
                user_id = self.user_id,
                language=self.current_language,
                mode="Story",
                response=user_response
            )
        self.next_question()

    def next_question(self):
        # Progress to next round or show results if game is over
        if self.current_round < self.total_rounds:
            self.current_round += 1
            self.start_new_round()
        else:
            self.show_results()

    def show_results(self):
        try:
            # Remove game frame
            for widget in self.root.winfo_children():
                if isinstance(widget, Frame) and widget.winfo_y() > 0:
                    widget.destroy()
                    
            # Create and display results frame
            result_frame = Frame(
                self.root,
                bg="#FFFCEE"
            )
            result_frame.place(x=0, rely=0.1, relwidth=1, relheight=0.9)
            
            # Display completion message
            Label(
                result_frame,
                text="Story Mode Over!",
                font=FONT_STYLES['message'],
                fg='black',
                bg="#FFFCEE"
            ).pack(pady=20)
            
            # Show final round count
            Label(
                result_frame,
                text=f"Completed {self.total_rounds} Rounds!",
                font=FONT_STYLES['entry'],
                fg='black',
                bg="#FFFCEE"
            ).pack(pady=10)
            
            self.root.update()  # Force UI update
            
        finally:
            # Ensure database connections are closed
            self.cursor.close()
            self.db.close()
class WritingModeStart:
    def __init__(self, root, user_id, language):
        self.root = root
        self.user_id = user_id
        
        # Language mapping
        self.languages = {
            'English': 'eng', 'German': 'deu', 'Spanish': 'spa', 'French': 'fra',
            'Japanese': 'jpn', 'Korean': 'kor', 'Portuguese': 'por', 'Italian': 'ita',
            'Persian': 'fas', 'Indonesian': 'ind', 'Chinese': 'zho', 'Russian': 'rus',
            'Turkish': 'tur', 'Moroccan Arabic': 'ary', 'Arabic': 'arb'
        }
        
        self.db = Database()
        self.cursor = self.db.cursor
        
        # Initialize response tracker
        self.response_tracker = ResponseTracker(self.db)
        
        # Game state initialization
        self.current_round = 1
        self.total_rounds = 10
        self.image_dir = r"/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/twemoji_final_png"
        self.current_emojis = []
        self.current_language = language
        self.current_emoji = None  # Added to store current emoji data
        
        # Setup UI
        self.setup_ui()
        
        # Start first round
        self.start_new_round()

    def setup_ui(self):
        # Container frame with padding
        container = Frame(
            self.root,
            bg='#FFFCEE',
            padx=20
        )
        container.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            container,
            orient='horizontal',
            length=760,
            maximum=self.total_rounds,
            variable=self.progress_var,
            mode='determinate',
            style="Pink.Horizontal.TProgressbar"
        )
        self.progress_bar.place(relx=0, rely=0.05)

        # Emoji frame for displaying images
        self.emoji_frame = Frame(
            container,
            bg='#FFFCEE'
        )
        self.emoji_frame.place(relx=0.5, rely=0.2, anchor='center')
        
        # Answer label for showing correct answer
        self.answer_label = Label(
            container,
            text="",
            font=('pretendard', 14, 'bold'),
            fg='blue',
            bg='#FFFCEE',
            wraplength=700
        )
        self.answer_label.place(relx=0.5, rely=0.4, anchor='center')

        # Text input
        self.text_input = Text(
            container,
            height=8,
            width=40,
            font=('pretendard', 14, 'bold'),
            relief="solid",
            bd=1,
            fg='black',
            bg='#F4D2FF'
        )
        self.text_input.place(relx=0.5, rely=0.6, anchor='center')
        
        self.text_input.insert('1.0', "Make your story with Emojis")
        self.text_input.config(fg='#F4D2FF')
        self.text_input.bind('<FocusIn>', self.on_entry_click)
        self.text_input.bind('<FocusOut>', self.on_focus_out)

        # Button frame
        button_frame = Frame(
            container,
            bg='#FFFCEE'
        )
        button_frame.place(relx=0.5, rely=0.85, anchor='center')

        # Submit button
        self.submit_button = Button(
            button_frame,
            text="Submit",
            command=self.check_answer,
            font=FONT_STYLES['label'],
            bg="#45CF8F",
            width=100
        )
        self.submit_button.pack(side='left', padx=5)

        # Pass button
        self.pass_button = Button(
            button_frame,
            text="Pass",
            command=self.next_question,
            font=FONT_STYLES['label'],
            bg="#FFD700",
            width=100
        )
        self.pass_button.pack(side='left', padx=5)

    def change_language(self):
        """Handle language change"""
        selected_language = self.language_var.get()
        self.current_language = self.languages[selected_language]

    def on_entry_click(self, event):
        if self.text_input.get('1.0', 'end-1c') == "Please type it....":
            self.text_input.delete('1.0', tk.END)
            self.text_input.config(fg='black')

    def on_focus_out(self, event):
        if self.text_input.get('1.0', 'end-1c') == '':
            self.text_input.insert('1.0', "Please type it....")
            self.text_input.config(fg='grey')

    def start_new_round(self):
        # Clear previous emojis and reset answer label
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
        self.answer_label.config(text="")

        # Select random emoji with description
        query = f"""
        SELECT eb.idx, ed.description_{self.current_language} as description
        FROM emoji_basic eb
        JOIN emoji_description ed ON eb.idx = ed.idx
        WHERE ed.description_{self.current_language} IS NOT NULL
        ORDER BY RAND()
        LIMIT 1
        """
        self.cursor.execute(query)
        self.current_emoji = self.cursor.fetchone()

        # Display emoji image
        image_filename = f"twemoji_{self.current_emoji['idx']}.png"
        image_path = os.path.join(self.image_dir, image_filename)
        
        if os.path.exists(image_path):
            image = Image.open(image_path)
            image = image.resize((70, 70), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            emoji_label = Label(
                self.emoji_frame,
                image=photo,
                bg='#FFFCEE'
            )
            emoji_label.image = photo
            emoji_label.pack(side='left', padx=5)

        # Reset text input
        self.text_input.delete('1.0', tk.END)
        self.text_input.insert('1.0', "Please type it....")
        self.text_input.config(fg='grey')
        
        # Update round display and progress
        self.progress_var.set(self.current_round - 1)

    def check_answer(self):
        user_response = self.text_input.get('1.0', 'end-1c').strip()
        if user_response and user_response != "Please type it....":
            self.response_tracker.log_response(
                user_id=self.user_id,
                language=self.current_language,
                mode="Writing",
                response=user_response
            )
        
        # Show the answer
        correct_answer = self.current_emoji['description']
        self.answer_label.config(text=f"Answer: {correct_answer}")
        
        # Wait a moment before moving to next question
        self.root.after(2000, self.next_question)

    def next_question(self):
        if self.current_round < self.total_rounds:
            self.current_round += 1
            self.start_new_round()
        else:
            self.show_results()

    def show_results(self):
        try:
            # Remove existed game frame
            for widget in self.root.winfo_children():
                if isinstance(widget, Frame) and widget.winfo_y() > 0:
                    widget.destroy()
                    
            # Make a New Result frame and display it 
            result_frame = Frame(
                self.root,
                bg="#FFFCEE"
            )
            result_frame.place(x=0, rely=0.1, relwidth=1, relheight=0.9)
            
            # Results window title
            Label(
                result_frame,
                text="Writing Mode Over!",
                font=FONT_STYLES['message'],
                fg='black',
                bg="#FFFCEE"
            ).pack(pady=20)
            
            # Final round display
            Label(
                result_frame,
                text=f"Completed {self.total_rounds} Rounds!",
                font=FONT_STYLES['entry'],
                fg='black',
                bg="#FFFCEE"
            ).pack(pady=10)
            
            self.root.update()  
            
        finally:
            # DB close
            self.cursor.close()
            self.db.close()

# Function Definition 'clear_window'
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

# Function Definition for 'show_onboarding_frame'
def show_onboarding_frame():
    clear_window()

    frame = Frame(root)
    frame.place(relwidth=1, relheight=1)

    # Get background image
    global bg_image
    bg_image = ImageTk.PhotoImage(Image.open("/Users/choseungwoo/Desktop/skku/24_Fall_Relational-DB/Python/image/background.png"))

    bg_label = Label(
        frame,
        image = bg_image
        )
    bg_label.place(relwidth = 1, relheight = 1)

    container_frame = Frame(
        frame,
        bg="SystemTransparent", # if Window OS, 'transparent'
        width=300,
        height=300
        )
    container_frame.pack(pady=150)

    # Create title label
    title_label = Label(
        container_frame,
        text="Emo-Quiz",
        font=('Hanalei Fill', 40, 'bold'),
        fg="black",
        bg="SystemTransparent" # if Window OS, 'transparent'
    )
    title_label.pack(pady=20)
    
    # Create button for Staring App
    start_button = Button(
        container_frame,
        text="START",
        bg="#321A1F",
        fg="#FEC833",
        font=FONT_STYLES['button'],
        width=260,
        height=50,
        command=show_login_frame
    )
    start_button.pack(pady=20)
    
# Function Definition for 'show_login_frame'
def show_login_frame():
    global language_option

    # Clear the frame
    clear_window()

    frame = Frame(
        root,
        bg="#FFFCEE"
    )
    frame.pack(fill='both', expand=True)
    
    # Create a title frame
    title_label = Label(
        frame,
        text="Emo-Quiz",
        font=('Hanalei Fill', 40, 'bold'),
        fg="black",
        bg="#FFFCEE"
    )
    title_label.pack(pady=20)
    
    container_frame = Frame(
        frame,
        bg="#FFFCEE",
        width=300,
        height=300
        )
    container_frame.pack()

    container_frame.pack_propagate(False)

    def on_focus_in(event):
        if nickname_entry.get() == "Enter Nickname":
            nickname_entry.delete(0, END)
            nickname_entry.config(fg='black')

    def on_focus_out(event):
        if nickname_entry.get().strip() == "":
            nickname_entry.delete(0, END)
            nickname_entry.insert(0, "Enter Nickname")
            nickname_entry.config(fg='gray')

    nickname_entry = Entry(
        container_frame,
        font=FONT_STYLES['label'],
        fg="gray",  # placeholder 색상
        bg="#FFF5D1"
    )
    nickname_entry.insert(0, "Enter Nickname")
    nickname_entry.bind('<FocusIn>', on_focus_in)
    nickname_entry.bind('<FocusOut>', on_focus_out)

    nickname_entry.pack(pady=10, fill='x', padx=20)
    
    language_option.set("Select language")
    drop_language = OptionMenu(
        container_frame,
        language_option,
        "Korean", "English", "Chinese", "Spanish", "German", "French", 
        "Japanese", "Portuguese", "Italian", "Persian", "Indonesian", 
        "Russian", "Turkish", "Moroccan Arabic", "Modern Standard Arabic"
    )
    drop_language.config(
        font=FONT_STYLES['label'],
        fg="black",
        bg="#FFF5D1"
    )
    drop_language.pack(pady=20, fill='x', padx=20)
    
    login_button = Button(  # 로그인 버튼
        container_frame,
        text="Log in",
        command=lambda: login_action(nickname_entry.get()),
        bg="#FFD700",
        fg="black",
        font=FONT_STYLES['button'],
        height=50
    )
    login_button.pack(pady=30, fill='x', padx=20)

# Function Definition for 'login_action' (real action with DB)
def login_action(nickname):
    global current_nickname
    global current_user_id

    if nickname == "Enter Nickname" or not nickname.strip():
        messagebox.showerror("Error", "Please enter a nickname")
        return

    db = Database()
    cursor = db.cursor
    
    # Confirm if the user already exists
    cursor.execute("SELECT user_id, user_name FROM user WHERE user_name = %s", (nickname,))
    user = cursor.fetchone()
    
    if user:
        # old user
        user_id = user['user_id']
        current_nickname = user['user_name']
        current_user_id = user_id
        messagebox.showinfo("Welcome back!", f"Welcome back, {current_nickname}!")
    else:
        # new user
        try:
            cursor.execute("INSERT INTO user (user_name) VALUES (%s)", (nickname,))
            db.commit()
            user_id = cursor.lastrowid
            current_nickname = nickname
            current_user_id = user_id
            messagebox.showinfo("Welcome!", f"Welcome! {current_nickname}")
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to register new user: {err}")
            db.close()
            return
        
    db.close()
    show_menu_frame(current_nickname)

# Function Definition for 'show_navigation'
def show_navigation(nickname):
    global current_screen
    global current_nickname
    current_nickname = nickname  # 닉네임 저장

    # Create a main frame
    nav_frame = Frame(
        root,
        bg='#FFF5D1'
    )
    nav_frame.place(relx=0, rely=0, relwidth=1, relheight=0.1)
    
    # Create a frame for label
    label_frame = Frame(
        nav_frame,
        bg="#FFFFFF"
    )
    label_frame.place(relx=0.02, rely=0.3, relwidth=0.3, relheight=0.4)

    # Create a label for user name
    user_info_label = Label(
        label_frame,
        text=f"Hi, {nickname}!",
        font=FONT_STYLES['label'],
        fg='black',
        bg="#FFF5D1",
        anchor='w',
        padx=10
    )
    user_info_label.pack(fill='x')
    
    # Function Definition 'back'
    def go_back():
        global current_nickname
        if current_screen == "menu":
            show_login_frame()
            current_nickname = ""
        elif current_screen == "study":
            show_menu_frame(current_nickname)
        elif current_screen == "practice":
            show_menu_frame(current_nickname)
        elif current_screen == "challenge":
            show_menu_frame(current_nickname)
        elif current_screen == "profile":
            show_menu_frame(current_nickname)

    back_button = Button(
        nav_frame,
        text="Back",
        font=FONT_STYLES['small'],
        bg="#FFD700",
        command=go_back
    )
    back_button.place(relx=0.85, rely=0.3, relwidth=0.1, relheight=0.4)

# Function Definition for 'show_menu_frame'
def show_menu_frame(current_nickname):
    global current_screen
    current_screen = "menu"

    # Clear the frame and Show navigation again before menu
    clear_window()
    show_navigation(current_nickname)

    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    
    # Create buttons for menu
    Buttons = [
        ("Study", show_study_frame, "#45CF8F"),
        ("Practice", show_practice_frame, "#45CF8F"),
        ("Challenge", show_challenge_frame, "#45CF8F"),
        ("Profile", show_profile_frame, "#45CF8F"),
    ]
    for text, command, color in Buttons:
        button_practice = Button(
            frame,
            text=text,
            command=command,
            bg=color,
            font=FONT_STYLES['button'],
            width=200,
            height=50
        )
        button_practice.pack(pady=10)

# Study Mode
def show_study_frame():
    global current_screen
    current_screen = "study"

    # Clear the frame and Show navigation again before starting Study mode
    clear_window()
    show_navigation(current_nickname)

    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    
    Buttons = [
        ("My Responses", show_myResponse_frame, "#61F9B3"),
        ("Story Mode", show_storyMode_frame, "#61F9B3"),
        ("Writing Mode", show_WritingMode_frame, "#61F9B3"),
        ("Flashcard", show_flashcard_frame, "#61F9B3"),
    ]
    for text, command, color in Buttons:
        button_practice = Button(
            frame,
            text=text,
            command=command,
            bg=color,
            font=FONT_STYLES['button'],
            width=200,
            height=50
        )
        button_practice.pack(pady=10)
def show_myResponse_frame():
    global current_screen
    current_screen = "study"

    # Clear the frame and Show navigation again before viewing My Responses view
    clear_window()
    show_navigation(current_nickname)

    # Create a main frame
    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    
    response_viewer = ResponseViewer(root, current_user_id)
def show_flashcard_frame():
    global current_screen
    current_screen = "study"

    clear_window()
    show_navigation(current_nickname)

    # Create a main frame
    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    
    flashcard = FlashcardModeStart(root)    
def show_storyMode_frame():
    global current_screen
    current_screen = "study"

    # Clear the frame and Show navigation again before starting Story mode
    clear_window()
    show_navigation(current_nickname)

    # Create a main frame
    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    
    storyModeLabel = Label(
        frame,
        text="Make a short story with 5 Emojis!",
        font=FONT_STYLES['button'],
        fg="black",
        bg='#FFFCEE'
    )
    storyModeLabel.pack(pady=50)

    def startStoryMode():
        global language_option
        
        # Dictionary for language mapping
        language_mapping = {
            "Korean": "kor", "English": "eng", "Chinese": "zho", "Spanish": "spa",
            "French": "fra", "Japanese": "jpn", "Portuguese": "por",
            "Italian": "ita", "Persian": "fas", "Indonesian": "ind",
            "Russian": "rus", "Moroccan Arabic": "ary", "Modern Standard Arabic": "arb"
        }

        # Get selected laguage from Global variable
        current_language = language_mapping.get(language_option.get())

        # Clear the frame and Show navigation again before starting Story mode
        clear_window()
        show_navigation(current_nickname)

        # Get selected laguage from Global variable
        game_frame = Frame(
            root,
            bg="#FFFCEE",
            pady=30
        )
        game_frame.place(
            x=0,
            rely=0.1,
            relwidth=1,
            relheight=0.9
        )

        # Create instances for Story mode
        storyMode = StoryModeStart(
            root,
            user_id=current_user_id,
            language = current_language
        )
    
    # Create a button for Starting a game
    start_button = Button(
        frame,
        text="Game Start!",
        command=startStoryMode,
        bg="#FFD700",
        fg="black",
        font=FONT_STYLES['button'],
        width=200,
        height=50
    )
    start_button.place(relx=0.5, rely=0.4, anchor='center')

# Function Definition for 'show_WritingMode_frame'
def show_WritingMode_frame():
    global current_screen
    current_screen = "study"

    # Clear the frame and Show navigation again before starting Writing mode
    clear_window()
    show_navigation(current_nickname)

    # Creat a frame for game
    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    
    storyModeLabel = Label(
        frame,
        text="Let's Describe Emoji!",
        font=FONT_STYLES['button'],
        fg="black",
        bg='#FFFCEE'
    )
    storyModeLabel.pack(pady=50)

    def startStoryMode():
        global language_option
        
        # Dictionary for language mapping
        language_mapping = {
            "Korean": "kor", "English": "eng", "Chinese": "zho", "Spanish": "spa",
            "French": "fra", "Japanese": "jpn", "Portuguese": "por",
            "Italian": "ita", "Persian": "fas", "Indonesian": "ind",
            "Russian": "rus", "Moroccan Arabic": "ary", "Modern Standard Arabic": "arb"
        }

        # Get selected laguage from Global variable
        current_language = language_mapping.get(language_option.get())

        # Clear the frame and Show navigation again before starting Story mode
        clear_window()
        show_navigation(current_nickname)

        # Creat a frame for game
        game_frame = Frame(
            root,
            bg="#FFFCEE",
            pady=30
        )
        game_frame.place(
            x=0,
            rely=0.1,
            relwidth=1,
            relheight=0.9
        )

        # Create instances for Writing mode
        storyMode = WritingModeStart(
            root,
            user_id=current_user_id,
            language = current_language
        )
    
    # Create a button for starting Writing mode
    start_button = Button(
        frame,
        text="Game Start!",
        command=startStoryMode,
        bg="#FFD700",
        fg="black",
        font=FONT_STYLES['button'],
        width=200,
        height=50
    )
    start_button.place(relx=0.5, rely=0.4, anchor='center')

# Practice Mode
def show_practice_frame():
    global current_screen
    current_screen = "practice"

    # Clear the frame and Show navigation again before starting Practice mode
    clear_window()
    show_navigation(current_nickname)

    # Create a Main frame
    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )

    container_frame = Frame(
        frame,
        bg="#FFFCEE",
        width=300,
        height=500
        )
    container_frame.pack()
    container_frame.pack_propagate(False) # Make the size of container frame not resizable

    # Create a label 'Difficulty'
    difficulty_label = Label(
        container_frame,
        text="Difficulty:",
        font=FONT_STYLES['label'],
        fg='black',
        bg="#FFFCEE"
    )
    difficulty_label.place(relx=0, rely=0)

    difficulty_frame = Frame(
        container_frame,
        bg="#FFFCEE",
        height=300
        )
    difficulty_frame.place(relx=0.4, rely=0, relwidth=0.6, relheight=0.3)
    difficulty_frame.pack_propagate(False)

    # Create a radio button UI for category
    difficulty_var = StringVar(value="Easy")
    for i, diff in enumerate(['Easy', 'Intermediate', 'Hard']):
        Radiobutton(
            difficulty_frame,
            text=diff,
            variable=difficulty_var,
            value=diff.lower(),
            fg='black',
            bg="#FFFCEE",
            font=FONT_STYLES['label'],
            anchor='w'
        ).grid(row=i+1, column=0, padx=5, sticky='w')

    # Create a label 'Category'
    category_label = Label(
        container_frame,
        text="Category:",
        font=FONT_STYLES['label'],
        fg='black',
        bg="#FFFCEE"
    )
    category_label.place(relx=0, rely=0.3)

    category_frame = Frame(
        container_frame,
        bg="#FFFCEE",
        height=300
        )
    category_frame.place(relx=0.4, rely=0.3, relwidth=0.6, relheight=0.3)
    category_frame.pack_propagate(False)

    # Create a Dropdown UI for category
    category_var = StringVar(value="All categories")
    categories = [
        'Food & Drink',
        'Animals & Nature',
        'Smileys & Emotion',
        'Travel & Places',
        'Objects',
        'Activities',
        'Symbols',
        'People & Body',
        'Flags',
        'All categories'
    ]
    category_menu = OptionMenu(
        category_frame,
        category_var,
        *categories
    )
    category_menu.grid(row=1, column=1, columnspan=3, sticky='ew', padx=5)
    category_menu.config(font=FONT_STYLES['small'])

    # Function Definition to start game
    def start_practice():
        global language_option

        # Create instances for EmojiGame
        language_mapping = {
            "Korean": "kor", "English": "eng", "Chinese": "zho", "Spanish": "spa",
            "French": "fra", "Japanese": "jpn", "Portuguese": "por",
            "Italian": "ita", "Persian": "fas", "Indonesian": "ind",
            "Russian": "rus", "Moroccan Arabic": "ary", "Modern Standard Arabic": "arb"
        }
        
        # Get selected laguage from Global variable
        current_language = language_mapping.get(language_option.get())
        
        # Clear the frame and Show navigation again before starting Practice mode
        clear_window()
        show_navigation(current_nickname)

        # Create a frmae for game
        game_frame = Frame(
            root,
            bg="#FFFCEE",
            pady=30
        )
        game_frame.place(
            x=0,
            rely=0.1,
            relwidth=1,
            relheight=0.9
        )

        # Create instances for Practice mode
        global game_instance
        game_instance = PracticeModeStart(
            game_frame,  # 메인 프레임을 부모로 전달
            user_id=current_user_id,
            language=current_language,
            difficulty=difficulty_var.get(),
            category=category_var.get()
        )

    # Create a start button
    start_button = Button(  # 게임 시작 버튼
        container_frame,
        text="Game Start!",
        command=start_practice,
        bg="#FFD700",
        fg="black",
        font=FONT_STYLES['button'],
        width=200,
        height=50
    )
    start_button.place(relx=0.5, rely=0.65, anchor='center')

# Function Definition 'show_challenge_frame'
def show_challenge_frame():
    global current_screen
    current_screen = "challenge"

    clear_window()
    show_navigation(current_nickname)
    
    # Create the main frame
    frame = Frame(
        root,
        bg="#FFFCEE",
        pady=30
    )
    frame.place(
        x=0,
        rely=0.1,
        relwidth=1,
        relheight=0.9
    )
    def start_challenge():
        global game_instance
        clear_window()
        show_navigation(current_nickname)

        # Dictionary for language mapping
        language_mapping = {
            "Korean": "kor",
            "English": "eng",
            "Chinese": "zho",
            "Spanish": "spa",
            "French": "fra",
            "Japanese": "jpn",
            "Portuguese": "por",
            "Italian": "ita",
            "Persian": "fas",
            "Indonesian": "ind",
            "Russian": "rus",
            "Turkish": "tur",
            "Moroccan Arabic": "ary",
            "Modern Standard Arabic": "arb"
        }

        # Creaete a frame for starting survival mode
        game_frame = Frame(
            root,
            bg="#FFFCEE",
            pady=30
        )
        game_frame.place(
            x=0,
            rely=0.1,
            relwidth=1,
            relheight=0.9
        )
        
        current_language = language_mapping.get(language_option.get())

        # Create instances for Survival mode
        game_instance = SurvivalModeStart(
            game_frame,
            user_id=current_user_id,
            language=current_language
        )

    start_button = Button(
        frame,
        text="Start Challenge",
        command=start_challenge,
        bg="#FFD700",
        fg="black",
        font=FONT_STYLES['button'],
        width=200,
        height=50
    )
    start_button.pack(pady=180)

# Function Definition 'show_profile_frame'
def show_profile_frame():
    global current_screen
    current_screen = "profile"

    clear_window()
    show_navigation(current_nickname)
    
    frame = Frame(
        root,
        bg="#FFFCEE"
    )
    frame.place(x=0, rely=0.1, relwidth=1, relheight=0.9)

    # Ranking Section
    ranking_frame = Frame(
        frame,
        bg='#FFFCEE'
    )
    ranking_frame.pack(fill='x', padx=20, pady=10)
    
    # Ranking Label
    Label(
        ranking_frame,
        text="🏆 Top 5 Ranking",
        font=FONT_STYLES['button'],
        fg="black",
        bg='#FFFCEE'
    ).pack(pady=10)
    
    # Ranking Table Style
    style = ttk.Style()
    style.configure(
        "Custom.Treeview",
        font=FONT_STYLES['small'],
        rowheight=30,
        background="#2C2C2C",
        fieldbackground="#2C2C2C",
        foreground="white"
    )
    style.configure(
        "Custom.Treeview.Heading",
        font=FONT_STYLES['small'],
        background="#1E1E1E",
        foreground="white"
    )

    # Create Ranking Table
    rank_table = ttk.Treeview(
        ranking_frame,
        columns=("Rank", "User", "Score", "Language"),
        show="headings",
        height=5,
        style="Custom.Treeview"
    )
    
    rank_table.heading("Rank", text="Rank") # Define Headers
    rank_table.heading("User", text="User")
    rank_table.heading("Score", text="Score")
    rank_table.heading("Language", text="Language")
    
    rank_table.column("Rank", width=150)
    rank_table.column("User", width=200)
    rank_table.column("Score", width=170)
    rank_table.column("Language", width=200)
    
    # Get Ranking data from DB
    db = Database()
    cursor = db.cursor
    
    # Get the highest score from 'best_score JSON'
    ranking_query = """
    SELECT u.user_name, 
           languages.language,
           JSON_EXTRACT(u.best_score, CONCAT('$."', language, '"')) as score
    FROM user u
    CROSS JOIN JSON_TABLE(
        '[{"language":"kor"},{"language":"eng"},{"language":"jpn"}]',
        '$[*]' COLUMNS (language VARCHAR(10) PATH '$.language')
    ) as languages
    WHERE JSON_EXTRACT(u.best_score, CONCAT('$."', language, '"')) IS NOT NULL
    ORDER BY CAST(score AS UNSIGNED) DESC
    LIMIT 5
    """
    cursor.execute(ranking_query)
    rankings = cursor.fetchall()

    for i, rank in enumerate(rankings, 1):
        rank_table.insert("", "end", values=(
            f"{i}.",
            rank['user_name'],
            rank['score'],
            rank['language']
        ))
    
    rank_table.pack(padx=10, pady=10)
    
    # Wrong Answers Section
    wrong_frame = Frame(
        frame,
        bg='#FFFCEE'
    )
    wrong_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    # Wrong Answers label
    Label(
        wrong_frame,
        text="❌ Wrong Answers (Practice Mode)",
        font=FONT_STYLES['button'],
        fg="black",
        bg='#FFFCEE'
    ).pack(pady=10)
    
    # Wrong Answers Table
    wrong_table = ttk.Treeview(
        wrong_frame,
        columns=("Language", "Difficulty", "Wrong Answer"),
        show="headings",
        height=10,
        style="Custom.Treeview"
    )
    
    wrong_table.heading("Language", text="Language")
    wrong_table.heading("Difficulty", text="Difficulty")
    wrong_table.heading("Wrong Answer", text="Wrong Answer")
    
    wrong_table.column("Language", width=100)
    wrong_table.column("Difficulty", width=120)
    wrong_table.column("Wrong Answer", width=500)
    
    # Get wrong answers from game_log
    wrong_query = """
    SELECT 
        gl.game_language,
        gl.difficulty,
        ed.description_eng as wrong_answer
    FROM game_log gl
    JOIN emoji_description ed ON gl.correct_idx = ed.idx
    WHERE gl.user_id = %s
    ORDER BY gl.correct_idx DESC
    """
    cursor.execute(wrong_query, (current_user_id,))
    wrong_answers = cursor.fetchall()
    
    for wrong in wrong_answers:
        wrong_table.insert("", "end", values=(
            wrong['game_language'],
            wrong['difficulty'],
            wrong['wrong_answer']
        ))
    
    wrong_table.pack(padx=10, pady=10)
    
    # Cleanup
    db.close()

# Starting Application
show_onboarding_frame()
root.mainloop()