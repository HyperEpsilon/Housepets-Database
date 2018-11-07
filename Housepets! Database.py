# Librarys
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pprint import pprint
import sqlite3

connection = None
cursor = None

def connect(path):
    global connection, cursor

    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    connection.commit()
    return

def define_tables():
    global connection, cursor

    comic_query=   '''
                        CREATE TABLE IF NOT EXISTS comic (
                                    comic_id INT,
                                    date DATE,
                                    title TEXT,
                                    alt_text TEXT,
                                    url TEXT,
                                    next_comic TEXT,
                                    PRIMARY KEY (comic_id)
                                    );
                    '''

    character_query=  '''
                        CREATE TABLE IF NOT EXISTS  character (
                                    name TEXT,
                                    species TEXT,
                                    PRIMARY KEY (name)
                                    );
                    '''

    tag_query= '''
                    CREATE TABLE IF NOT EXISTS tag (
                                comic_id TEXT,
                                name TEXT,
                                PRIMARY KEY (comic_id, name),
                                FOREIGN KEY(comic_id) REFERENCES comic(comic_id) ON DELETE CASCADE,
                                FOREIGN KEY(name) REFERENCES character(name) ON DELETE CASCADE
                                );
                '''
    
    
    
    cursor.execute(comic_query)
    cursor.execute(character_query)
    cursor.execute(tag_query)
    connection.commit()

    return


def drop_tables():
    global connection, cursor
    drop_tables = ['tag', 'character', 'comic']
    for table in drop_tables:
        cursor.execute('drop table if exists {}'.format(table))    

def make_soup(comic_page):
    page = urlopen(comic_page)
    return BeautifulSoup(page, 'html.parser')    

def get_comic_id(soup):
    ## Extract the comic ID from the 'comic-wrap' div's class,
    ## then return it as an int
    
    c_id = soup.find('div', attrs = {'id':'comic-wrap'})['class'][0]
    c_id = c_id.split('-')[2]
    c_id = int(c_id)
    
    return c_id

def get_date(soup):
    ## Extract the comic date from the comic URL, then convert it
    ## into an SQL compatible date format
    
    date = soup.find('link', attrs = {'rel':'canonical'})['href']
    date = '-'.join(date.split('/')[4:7])
    
    return date

def get_title(soup):
    ## Extract the comic title from the title header
    
    title = soup.find('h1', attrs = {'class':'entry-title'}).get_text()
    
    return title

def get_alt_text(soup):
    alt_text = soup.find('div', attrs = {'id':'comic'})
    alt_text = alt_text.find('img')['alt']
    
    return alt_text

def get_next_comic(soup):
    next_comic = soup.find('td', attrs = {'class':'comic_navi_right'})
    next_comic = next_comic.find('a', attrs = {'class':'navi comic-nav-next navi-next'})
    if next_comic == None:
        return None
    
    next_comic = next_comic['href']
    
    return next_comic

def get_tags(soup):
    tags = soup.find_all('a', attrs = {'rel':'tag'})
    for c,tag in enumerate(tags):
        tags[c] = tag.get_text()
    
    return tags

def add_comic(comic_id, date, title, alt_text, url, next_comic):
    data = (comic_id, date, title, alt_text, url, next_comic)
    
    try:
        cursor.execute('INSERT INTO comic (comic_id, date, title, alt_text, url, next_comic) VALUES (?,?,?,?,?,?)', data)
    except sqlite3.IntegrityError:
        pass    

def add_tag(comic_id, tag):
    try:
        cursor.execute('INSERT INTO tag (comic_id, name) VALUES (?,?)', (comic_id, tag))
    except sqlite3.IntegrityError as inst:
        if str(inst.args) == "('FOREIGN KEY constraint failed',)":
            cursor.execute('INSERT INTO character (name) VALUES (?)', (tag,))
            cursor.execute('INSERT INTO tag (comic_id, name) VALUES (?,?)', (comic_id, tag))
        else:
            print(inst.args)
            raise

def main():
    global connection, cursor
    
    # Implement method of grabing comic with next comic as null for start point
    # Also update the old row to include the new data
    comic_page = "http://www.housepetscomic.com/comic/2008/06/02/when-boredom-strikes/"
    
    try:
        path="./Housepets.db"
        connect(path)
        #connection.create_function('GPA', 1, GPA)
    
        #drop_tables()
        define_tables()        
        
        while comic_page:
        #for i in range(10):
            soup = make_soup(comic_page)
            
            comic_id = get_comic_id(soup)
            date = get_date(soup)
            title = get_title(soup)
            alt_text = get_alt_text(soup)
            next_comic = get_next_comic(soup)
            
            add_comic(comic_id, date, title, alt_text, comic_page, next_comic)
            
            tags = get_tags(soup)
            
            for tag in tags:
                add_tag(comic_id, tag)
    
            #pprint(tags)
            
            print(title)
            
            comic_page = next_comic
    
    except KeyboardInterrupt:
        pass
    
    finally:
        connection.commit()
        connection.close()
    
    return

if __name__ == "__main__":
    main()