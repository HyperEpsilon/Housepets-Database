select c1.date, c1.title, c1.name, c2.date, c2.title
from comic_tags c1, comic_tags c2
where c1.name = c2.name
and c1.date > c2.date