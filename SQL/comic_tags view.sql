create view comic_tags as
select comic_id, date, title, name, alt_text, url, next_comic
from comic inner join tag using (comic_id)