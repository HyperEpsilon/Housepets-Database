select 
  starttime.name as gapid, counter.appear as appearences, starttime.date as starttime, endtime.date as endtime, 
  /* Replace next line with your DB's way of calculating the gap */
  julianday(endtime.date) - julianday(starttime.date) as gap, 
  endtime.comic_id - starttime.comic_id as comic_diff,
  starttime.title, endtime.title
from 
  comic_tags as starttime
inner join comic_tags as endtime on 
  (starttime.char_id = endtime.char_id) 
  and (starttime.unix_date < endtime.unix_date) 
left join comic_tags as intermediatetime on 
  (starttime.char_id = intermediatetime.char_id) 
  and (starttime.unix_date < intermediatetime.unix_date) 
  and (intermediatetime.unix_date < endtime.unix_date)
inner join 
  (select char_id, count(*) appear
  from tag
  group by name
  having appear >= 10
  order by count(*) desc) as counter on (starttime.char_id = counter.char_id)
where 
  (intermediatetime.char_id is null)
order by gap desc