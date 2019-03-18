create database liuzichongqi;
use liuzichongqi;

/*
black平面记录黑子的位置,有子为1,无子为0;
white平面记录白子的位置,有子为1,无子为0;
rival_last_move_position平面记录对手最后一次走子后子的位置(该走动会造成吃子,所以猜测它可能对训练很重要);
is_current_black平面记录当前行棋方是不是先手,也即是不是黑棋,为先手时全为1,否则全为0;
serial 对局序列号,从1开始递增,指明是第几把对局,如果有时间加打谱功能,则该序列号也是必须的

其实只需要记录moves就可以了,其它都可以不管,直接init一个board,然后doMove就可以推导出其它数据
 */
show databases;
show tables;

drop table if exists game;
create table game(
  uuid char(36) primary key,
  states text,
  probabilities text,
  scores text,
  moves text,
  type varchar(20) comment 'train, evaluation, play',
  black varchar(20) comment 'AlphaZero, AlphaBeta, PureMCTS, Human',
  white varchar(20) comment 'AlphaZero, AlphaBeta, PureMCTS, Human',
  winner char(5) comment 'black, white, tie',
  insert_time datetime,
  network_version int comment 'Identify different network'
);

select * from game order by insert_time asc;
