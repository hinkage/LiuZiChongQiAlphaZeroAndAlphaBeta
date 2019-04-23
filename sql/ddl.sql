create database liuzichongqi;
use liuzichongqi;

/*
其实只需要记录moves就可以了,其它都可以不管,直接init一个board,然后doMove就可以推导出其它数据
 */
drop table if exists game;
create table game
(
  uuid            char(36) primary key,
  states          mediumtext,
  probabilities   mediumtext,
  scores          text,
  moves           text,
  moves_length    int,
  type            varchar(20) comment 'train, evaluation, play',
  black           varchar(20) comment 'AlphaZero, AlphaBeta, PureMCTS, Human',
  white           varchar(20) comment 'AlphaZero, AlphaBeta, PureMCTS, Human',
  winner          char(5) comment 'black, white, tie',
  insert_time     datetime,
  network_version int comment 'Identify different network'
);

drop table if exists policy_update;
create table policy_update
(
  uuid                         char(36) primary key,
  Kullback_Leibler_Divergence  decimal(23, 21),
  old_learning_rate_multiplier decimal(23, 21),
  new_learning_rate_multiplier decimal(23, 21),
  old_learning_rate            decimal(23, 21),
  new_learning_rate            decimal(23, 21),
  loss                         decimal(23, 21),
  entropy                      decimal(23, 21),
  old_variance                 decimal(23, 21),
  new_variance                 decimal(23, 21),
  insert_time                  datetime,
  type                         varchar(20) comment 'from_db, from_self_play'
);
