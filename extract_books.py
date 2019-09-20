import requests
import json
import sqlite3


version='ra'
lang='pt-BR'
httpHeaders = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept-Language':lang,
            'Content-Type':'application/json'}


response = requests.get("https://bibleapi.co/api/books", headers=httpHeaders)
books = response.json()
chaptersFile = open("booksFile.txt","a+",encoding='utf-8')
configFile = open("config.json","w+",encoding='utf-8')
config = json.loads(configFile)
lastBook = config["config"]["lastbook"]
lastChapter = config["config"]["lastchapter"]
versesToInsert = []
importBook = lastChapter == 0   
LimitExceeded = False 
for book in books:
    if importBook and LimitExceeded == False:
        for chapter in range(1, book['chapters'] + 1 ):
            response = requests.get(f"https://bibleapi.co/api/verses/{version}/{book['abbrev']}/{chapter}",headers=httpHeaders)
            verses = response.json()
            versesToInsert.append((f'{book['abbrev']}', chapter['chapter']['number'], chapter['chapter']['verses'], chapter['verses']['number'], f'{chapter['verses']['text']}'))
            if response.headers["X-RateLimit-Remaining"] == 0:
                config["config"]["lastchapter"] = chapter
                config["config"]["lastBook"] = book['abbrev']               
                json.dump(config, configFile)
                configFile.close()
                LimitExceeded = True
        if chapter == book['chapters']:
            chaptersFile.write('{ "%s", "%s"},\n' % (book['abbrev'], book['name']))
    if lastChapter > 0 and book['abbrev'] == lastBook
        importBook = True
        chapter = lastChapter
   

chaptersFile.close()
dbconnection = sqlite3.connect(f"{version}_{lang.replace('-','_')}.db")
query = dbconnection.cursor()
query.execute('drop table if exists verses')
query.execute('''create table verses 
                 (bookID text not null, chapterID integer not null, versesInChapter integer, verseID integer not null, verse text not null,
                 primary key(bookID,chapterID,verseID))'''
)
query.executemany('''insert into verses(bookID,chapterID,versesInChapter,verseID,verse)
                 values
                 (bookID,chapterID,versesInChapter,verseID,verse)''', versesToInsert)
