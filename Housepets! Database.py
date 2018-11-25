# Librarys
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pprint import pprint
import sqlite3, os, datetime

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
                                    comic_id INTEGER PRIMARY KEY,
                                    date DATE,
                                    unix_date INT,
                                    title TEXT,
                                    alt_text TEXT,
                                    url TEXT,
                                    next_comic TEXT
                                    );
                    '''

    character_query=  '''
                        CREATE TABLE IF NOT EXISTS  character (
                                    char_id INTEGER PRIMARY KEY,
                                    name TEXT,
                                    species TEXT,
                                    notes TEXT
                                    );
                    '''

    tag_query= '''
                    CREATE TABLE IF NOT EXISTS tag (
                                comic_id INT,
                                char_id INT,
                                name TEXT,
                                PRIMARY KEY (comic_id, char_id),
                                FOREIGN KEY(comic_id) REFERENCES comic(comic_id) ON DELETE CASCADE,
                                FOREIGN KEY(char_id) REFERENCES character(char_id) ON DELETE CASCADE
                                );
                '''
    
    
    
    cursor.execute(comic_query)
    cursor.execute(character_query)
    cursor.execute(tag_query)
    connection.commit()

    return

# Defines which tables to drop from the DB upon recreation
# Character is often excluded because there's a lot of manual entry
def drop_tables(*drop_tables):
    global connection, cursor
    for table in drop_tables:
        cursor.execute('drop table if exists {}'.format(table))    

def make_soup(comic_page):
    page = urlopen(comic_page)
    return BeautifulSoup(page, 'html.parser')    

def get_date(soup):
    ## Extract the comic date from the comic URL, then convert it
    ## into an SQL compatible date format and unix timestamp
    
    date = soup.find('link', attrs = {'rel':'canonical'})['href']
    date = '-'.join(date.split('/')[4:7])
    unix_date = int(datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).timestamp())
    
    return date, unix_date

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

def add_comic(date, unix_date, title, alt_text, url, next_comic):
    data = [date, unix_date, title, alt_text, url, next_comic]

    # Checks if the comic url is already in the database, adds it if it's not
    # and updates it if it is. It then returns whether to add tags for the comic
    if not cursor.execute("SELECT * FROM comic WHERE url=?", (url,)).fetchall():
        cursor.execute('INSERT INTO comic (date, unix_date, title, alt_text, url, next_comic) VALUES (?,?,?,?,?,?)', data)
        return True
    else:
        cursor.execute("UPDATE comic SET date = ?, unix_date = ?, title = ?, alt_text = ?, url = ?, next_comic = ? WHERE url = ?", data + [url])
        return False


def add_tag(comic_id, tag):
    char_id = cursor.execute("SELECT char_id FROM character WHERE name=?", (tag,)).fetchall()
    
    if not len(char_id):
        cursor.execute('INSERT INTO character (name) VALUES (?)', (tag,))
        char_id = int(cursor.lastrowid)
    else:
        char_id = char_id[0][0]
    
    cursor.execute('INSERT INTO tag (comic_id, char_id, name) VALUES (?,?,?)', (comic_id, char_id, tag))

def scrape(comic_page):
    while comic_page:
    #for i in range(10):
        soup = make_soup(comic_page)
        
        date, unix_date = get_date(soup)
        title = get_title(soup)
        alt_text = get_alt_text(soup)
        next_comic = get_next_comic(soup)
        
        add_tags = add_comic(date, unix_date, title, alt_text, comic_page, next_comic)
        comic_id = cursor.lastrowid
        
        if add_tags:
            tags = get_tags(soup)
            for tag in tags:
                add_tag(comic_id, tag)
        
        print(title)
        
        comic_page = next_comic    

def scrape_from_beginning():
    global connection, cursor
    
    path="./Housepets.db"
    connect(path)    
    
    comic_page = "http://www.housepetscomic.com/comic/2008/06/02/when-boredom-strikes/"
    
    try:
        #drop_tables('tag', 'comic', 'character')
        drop_tables('tag', 'comic')
        define_tables()        
        
        scrape(comic_page)
    
    except KeyboardInterrupt:
        pass
    
    finally:
        connection.commit()
        connection.close()
    
    return

def update_from_last():
    global connection, cursor
    
    path="./Housepets.db"
    connect(path)    
    
    try:
        comic_page = cursor.execute("select url FROM comic WHERE next_comic is Null").fetchall()[0][0]
    except (sqlite3.OperationalError, IndexError):
        scrape_from_beginning()
        return
    
    try:
        scrape(comic_page)
    
    finally:
        connection.commit()
        connection.close()    

def restore_character_data():
    backup = cursor.execute('''SELECT species, notes, name FROM character_backup''').fetchall()
    
    query = '''UPDATE character SET species = ?, notes = ? WHERE name = ?'''
    cursor.executemany(query, backup)
    connection.commit()
    connection.close()

def main():
    while True:
        option = -1
        confirmed = ""
        
        while option not in range(3):
            print("Housepets Database Management")
            print("(1) Create database from beginning")
            print("(2) Update database from last comic")
            print("(0) QUIT")
            
            option = input("Please select an option: ")
            try:
                option = int(option)
            except ValueError:
                pass
    
        if option == 0:
            return
        
        elif option == 1:
            while confirmed not in ('Y','N'):
                confirmed = input ("This will overwrite the current database. Are you sure? (Y/N) ").upper()
            os.system('cls')
            
            if confirmed == 'Y':
                scrape_from_beginning()
                return
        
        elif option == 2:
            os.system('cls')            
            update_from_last()
            return

if __name__ == "__main__":
    main()
