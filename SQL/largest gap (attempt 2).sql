select c1.name as name, julianday(c1.date) - julianday(c2.date) as time_gap, c1.date as date, c1.title as title, c2.date as last_date, c2.title as last_title, c1.comic_id as comic_id, c2.comic_id as last_comic_id
from comic_tags c1, comic_tags c2
where c1.name = c2.name
and c1.date > c2.date
and c2.date = (select max(c3.date)
				from comic_tags c3
				where c3.name = c1.name
				and c3.date < c1.date) 
order by time_gap desc