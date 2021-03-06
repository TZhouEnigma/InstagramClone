CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    FirstName varchar(255),
    LastName varchar(255),
    DOB DATE,
    password varchar(255),
    contribution int4,
    CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends (
    my_email varchar(255),
    friend_email varchar(255)
);
CREATE TABLE Albums(
    album_id int4 AUTO_INCREMENT,
    owner_uid int4,
    DOC DATE,
    Name varchar(255),
CONSTRAINT Albums_pk PRIMARY KEY (album_id)
);

#this is a relation table
CREATE TABLE HasPics(
album_id int4,
picture_id int4

);
CREATE TABLE Tags(
    tag_id int4 AUTO_INCREMENT,
    tagtext varchar(255) UNIQUE,
    CONSTRAINT Tags_pk PRIMARY KEY (tag_id)
);

#this is a relation table
CREATE TABLE TagPic(
    tag_id int4,
    picture_id int4,
     CONSTRAINT TagPic_pk PRIMARY KEY (tag_id,picture_id)
);

CREATE TABLE Likes(
    user_id int4,
    picture_id int4,
    CONSTRAINT Likes_pk PRIMARY KEY (user_id,picture_id)
);

CREATE TABLE Comments(
    comment_id int4 AUTO_INCREMENT,
    comment_owner_id int4,
    picture_id int4,
    comment_doc DATE,
    comment_text varchar(1000),
    CONSTRAINT Comments_pk PRIMARY KEY (comment_id) 
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4 NOT NULL,
  album_id int4 NOT NULL,
  imgdata longblob ,
  caption varchar(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);
INSERT INTO Users (FirstName,LastName,DOB,email, password,contribution) VALUES ('TERRY','ZHOU','2015-01-12','test@bu.edu', 'test',0);
INSERT INTO  Users (FirstName,LastName,DOB,email, password,contribution) VALUES ('TERRY','ZHOU','2015-01-12','test1@bu.edu', 'test2',0);
INSERT INTO Friends (my_email, friend_email) VALUES ('test@bu.edu', 'test1@bu.edu');
