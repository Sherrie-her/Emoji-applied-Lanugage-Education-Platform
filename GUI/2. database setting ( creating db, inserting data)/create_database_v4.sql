USE rdbmsfinal;

CREATE TABLE emoji_basic (
   idx INT PRIMARY KEY,
   emoji VARCHAR(10) NOT NULL,
   category VARCHAR(50) NOT NULL,
   codepoints VARCHAR(100) NOT NULL
);

CREATE TABLE emoji_description (
   idx INT PRIMARY KEY,
   description_eng TEXT NOT NULL,
   description_deu TEXT NOT NULL,
   description_spa TEXT NOT NULL, 
   description_fra TEXT NOT NULL,
   description_jpn TEXT NOT NULL,
   description_kor TEXT NOT NULL,
   description_por TEXT NOT NULL,
   description_ita TEXT NOT NULL,
   description_fas TEXT NOT NULL,
   description_ind TEXT NOT NULL,
   description_zho TEXT NOT NULL,
   description_rus TEXT NOT NULL,
   description_tur TEXT NOT NULL,
   description_ary TEXT NOT NULL,
   description_arb TEXT NOT NULL,
   FOREIGN KEY (idx) REFERENCES emoji_basic(idx)
);

CREATE TABLE user (
   user_id INT AUTO_INCREMENT PRIMARY KEY,
   user_name VARCHAR(100) NOT NULL,
   best_score JSON NOT NULL
);

CREATE TABLE practice_log (
   correct_idx INT NOT NULL,
   wrong_idx JSON NOT NULL,
   correct BOOLEAN NOT NULL,
   correct_description TEXT NOT NULL,
   difficulty ENUM('easy', 'intermediate', 'hard') NOT NULL,
   FOREIGN KEY (correct_idx) REFERENCES emoji_basic(idx)
);

CREATE TABLE game_log (
   user_id INT,
   game_language VARCHAR(10) NOT NULL,
   difficulty ENUM('easy', 'intermediate', 'hard') NOT NULL,
   correct_idx INT NOT NULL,
   FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE leaderboard (
   user_id INT,
   score JSON NOT NULL,
   FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE my_responses (
    user_id INT NOT NULL,
    date DATE NOT NULL,
    language VARCHAR(50) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
