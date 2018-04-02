create table users(
  id serial primary key,
  name text not NULL,
  password text not NULL,
  expert boolean not NULL ,
  admin boolean not NULL
);

create table questions(
  id serial primary key,
  question_text text not NULL ,
  answer_text text,
  asked_by_id INTEGER not NULL ,
  expert_id INTEGER  not NULL
);