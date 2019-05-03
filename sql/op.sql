use liuzichongqi;

select count(*) from game;

select
  insert_time, moves_length, type, black, white, winner, network_version
from game
order by insert_time desc limit 0, 500;

select black, white, winner from game where type='evaluation' order by insert_time asc;

select max(moves_length) from game;

select
  insert_time, moves_length, type, black, white, winner, network_version
from game
where type='show'
order by insert_time asc;

select * from game limit 0,5;

# 查询数据库大小
select concat(round(sum(data_length/1024/1024),2),'MB') as data from information_schema.tables where table_schema='liuzichongqi';

select * from policy_update order by insert_time desc;

# 吃谱总数及速度查询
select count(1), min(insert_time), max(insert_time), concat(60 * count(1) / timestampdiff(minute , min(insert_time), max(insert_time)), '谱/小时') from policy_update where type='from_db';

# 给一个较小的学习率,用于避免重启训练流水线时胜率严重下滑
insert into policy_update values('33c14066-6469-11e9-aa39-086266e2cb2c', 0, 0.2, 0.005, 0, 0, 0, 0, '2019-04-22 03:11:01', 'from_self_play');
insert into policy_update values('33c14066-6469-11e9-aa39-086266e2cb2c', 0.021749094128608704, 1.0, 0.005, 4.205149173736572, 4.133904933929443, -6.952383574954091e-05, 0.999079273918552, '2019-04-22 03:11:01', 'from_db');

# 注意以下为删除操作
# 删除之前的吃谱记录,重启吃谱前执行
delete from policy_update where insert_time <= '2019-04-27 08:37:10';
