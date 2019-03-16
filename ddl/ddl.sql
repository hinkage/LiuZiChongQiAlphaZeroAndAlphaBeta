create database liuzichongqi_final;
use liuzichongqi_final;

/*
black平面记录黑子的位置,有子为1,无子为0;
white平面记录白子的位置,有子为1,无子为0;
rival_last_move_position平面记录对手最后一次走子后子的位置(该走动会造成吃子,所以猜测它可能对训练很重要);
is_current_black平面记录当前行棋方是不是先手,也即是不是黑棋,为先手时全为1,否则全为0;
serial 对局序列号,从1开始递增,指明是第几把对局,如果有时间加打谱功能,则该序列号也是必须的
 */
drop table if exists board_data;
create table board_data(
  uuid char(36) primary key,
  type varchar(20) comment 'az_az_train, ab_az, az_ab, ab_ab, az_az',
  `black` char(16),
  white char(16),
  rival_last_move_position char(16),
  is_current_black char(16),
  move tinyint comment '[0, 63]',
  serial bigint(20),
  index (serial)
);

drop table if exists board_result;
create table board_result(
  uuid char(36) primary key,
  ref_serial bigint(20),
  winner char(5) comment 'black, white',
  constraint result_ref_serial
  foreign key result_ref_serial(ref_serial)
  references board_data(serial)
  on delete no action
  on update no action
);

insert into board_data (uuid, type, black, white, rival_last_move_position, is_current_black, move, serial)
values (uuid(), 'az_az_train', '0001', '0001', '0001', '1111', 23, 1);
insert into board_result (uuid, ref_serial, winner)
values (uuid(), 1, 'black');

select * from board_data;
select * from board_result;
select board_data.*, winner from board_data join board_result on board_result.ref_serial=board_data.serial;
