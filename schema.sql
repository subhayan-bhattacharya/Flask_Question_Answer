create table users(
  id INTEGER primary key autoincrement,
  name text not NULL,
  password text not NULL,
  expert boolean not NULL ,
  admin boolean not NULL
);

create table questions(
  id INTEGER primary key autoincrement,
  question_text text not NULL ,
  answer_text text,
  asked_by_id INTEGER not NULL ,
  expert_id INTEGER  not NULL
);