from __future__ import print_function
import requests
import json
import sqlite3
import sys
import os

#Loads config and log files
mode = 'r+' if os.path.exists('booksFile.txt') else 'w'
chaptersFile = open("booksFile.txt",mode,encoding='utf-8')
mode = 'r+' if os.path.exists('config.json') else 'w'
configFile = open("config.json",mode,encoding='utf-8')
jsonText = configFile.read()
config = json.loads(jsonText)
lastBook = config["config"]["lastbook"]
lastChapter = config["config"]["lastchapter"]
versesToInsert = []
booksToInsert = []
importBook = lastChapter == 0   
LimitExceeded = False 
versesImported = 0
#Calls BibleApi.co , RA version and PT-br language
version='ra'
lang='pt-BR'
httpHeaders = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept-Language':lang,
            'Content-Type':'application/json'}
response = requests.get("https://bibleapi.co/api/books", headers=httpHeaders)
books = response.json()
for book in books:
    print('\n####################################################')
    print(f"\nImporting book {book['name']}")
    print('\n####################################################')
    if importBook and LimitExceeded == False:
        for chapter in range(1, book['chapters'] + 1 ):
            print(f'\nChapter {chapter}\n')
            response = requests.get('https://bibleapi.co/api/verses/{}/{}/{}'.format(version,book['abbrev'],chapter),headers=httpHeaders)
            if response.status_code == 429:
                print('####################################################')
                print('API limit reached. Save to log and exiting.')
                print('####################################################')
                config["config"]["lastchapter"] = chapter
                config["config"]["lastBook"] = book['abbrev']               
                json.dump(config, configFile)
                LimitExceeded = True
            elif  response.status_code == 404:
                continue
            else:    
                verses = response.json()
                versesImported = 0
                for verse in verses['verses']:
                    versesToInsert.append({'{}'.format(book['abbrev']), verses['chapter']['number'], verses['chapter']['verses'], verse['number'], '{}'.format(verse['text'])})
                    versesImported += 1
                    print(f'{versesImported},', end=" ")
            
        if chapter == book['chapters']:
            chaptersFile.write('{ "%s", "%s"},\n' % (book['abbrev'], book['name']))
            booksToInsert.append({f"{book['abbrev']}", f"{book['name']}",book['chapters']})
            
    if lastChapter > 0 and book['abbrev'] == lastBook:
        importBook = True
        chapter = lastChapter
   
if configFile.closed == False:
    configFile.close()
if chaptersFile.closed == False:
    chaptersFile.close()
print('####################################################')
print('Writing data into SQlite database.')
print('####################################################')
with sqlite3.connect(f"{version}_{lang.replace('-','_')}.db") as dbconnection:
    query = dbconnection.cursor()
    query.execute('drop table if exists verses')
    query.execute('drop table if exists books')
    query.execute('''create table verses 
                    (bookID text not null, chapterID integer not null, versesInChapter integer, verseID integer not null, verse text not null,
                    primary key(bookID,chapterID,verseID))'''
    )
    query.execute('''create table books 
                    (bookID text not null, name text not null, chapters integer,
                    primary key(bookID))'''
    )
    query.executemany('''insert into verses(bookID, chapterID, versesInChapter, verseID, verse)
                    values
                    (?, ?, ?, ?, ?)''', versesToInsert)
    query.executemany('''insert into books(bookID,name,chapters)
                    values
                    (?, ?, ?)''', booksToInsert)
print('####################################################')
print('Process finished')
print('####################################################')
