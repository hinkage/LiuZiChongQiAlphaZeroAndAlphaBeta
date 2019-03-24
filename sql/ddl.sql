create database liuzichongqi;
use liuzichongqi;

/*
其实只需要记录moves就可以了,其它都可以不管,直接init一个board,然后doMove就可以推导出其它数据
 */
show databases;
show tables;

drop table if exists game;
create table game (
  uuid            char(36) primary key,
  states          mediumtext,
  probabilities   mediumtext,
  scores          text,
  moves           text,
  moves_length    int,
  type            varchar(20) comment 'train, evaluation, play',
  black           varchar(20) comment 'AlphaZero, alphaBeta, PureMCTS, Human',
  white           varchar(20) comment 'AlphaZero, alphaBeta, PureMCTS, Human',
  winner          char(5) comment 'black, white, tie',
  insert_time     datetime,
  network_version int comment 'Identify different network'
);

select count(*)
from game;

# 训练期间黑棋胜率

select
       insert_time, moves_length, type, black, white, winner, network_version
from game
order by insert_time asc;

select black, white, winner from game where type='evaluation' order by insert_time asc;

select max(moves_length) from game;

select
       insert_time, moves_length, type, black, white, winner, network_version
from game
where type='show'
order by insert_time asc;


