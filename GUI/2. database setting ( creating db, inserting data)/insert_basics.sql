LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/emoji_basic.csv'
INTO TABLE emoji_basic
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(idx, emoji, category, codepoints);

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/emoji_description.csv'
INTO TABLE emoji_description
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(idx, description_eng, description_deu, description_spa, description_fra, 
description_jpn, description_kor, description_por, description_ita, description_fas, 
description_ind, description_zho, description_rus, description_tur, description_ary, 
description_arb);