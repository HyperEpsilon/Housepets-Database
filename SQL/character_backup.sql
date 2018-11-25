drop table if exists character_backup;

create table character_backup (
		name TEXT,
		species TEXT,
		notes TEST,
		primary key (name)
		);

insert into character_backup
	select name, species, notes 
	from character
	where species is not null;