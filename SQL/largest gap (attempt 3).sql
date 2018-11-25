select 
  starttime.name as gapid, counter.appear as appearences, starttime.date as starttime, endtime.date as endtime, 
  /* Replace next line with your DB's way of calculating the gap */
  julianday(endtime.date) - julianday(starttime.date) as gap, starttime.title, endtime.title
from 
  comic_tags as starttime
inner join comic_tags as endtime on 
  (starttime.name = endtime.name) 
  and (starttime.date < endtime.date) 
left join comic_tags as intermediatetime on 
  (starttime.name = intermediatetime.name) 
  and (starttime.date < intermediatetime.date) 
  and (intermediatetime.date < endtime.date)
inner join 
  (select name, count(*) appear
  from tag
  group by name
  order by count(*) desc) as counter on (starttime.name = counter.name)
where 
  (intermediatetime.name is null)
order by gap desc