import os
from datetime import datetime

import requests
import sqlalchemy
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import bs4

DATABASE_URL = os.environ['DATABASE_URL']
DISCORD_ID = os.environ['CHESS_DISCORD_ID']
DISCORD_TOKEN = os.environ['CHESS_DISCORD_TOKEN']


def sendNotification(message):
    ID = DISCORD_ID
    TOKEN = DISCORD_TOKEN
    URL = f'https://discordapp.com/api/webhooks/{ID}/{TOKEN}'
    payload = {'content': message,
               'username': 'chess-maine-event-scraper',
               'avatar_url': 'http://chessmaine.net/chessmaine/templates/chessmaine2010/images/dkblue/logo.png'}
    return requests.post(URL, payload)


def getEvents():
    res = requests.get('http://chessmaine.net/chessmaine/events/')
    res.raise_for_status()
    noStarchSoup = bs4.BeautifulSoup(res.text, 'html.parser')
    events = noStarchSoup.select('.entry-header')
    return [item.getText() for item in events]


def getNewEvents(db, events):
    newEvents = []
    for event in events:
        query = db.query(Event).filter_by(title=event)
        ourEvent = query.all()
        if ourEvent == []:
            db.add(Event(title=event, scrape_dt=datetime.now()))
            db.commit()
            newEvents.append(event)
    return newEvents


def delOldEvents(db, events):
    oldEvents = []
    # this finds events in the db that are not in my scraped list
    query = db.query(Event).filter(~Event.title.in_(events))
    ourEvents = query.all()
    if ourEvents != []:
        for event in ourEvents:
            db.delete(event)
            db.commit()
            oldEvents.append(event.title)
    return oldEvents


Base = declarative_base()


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    scrape_dt = Column(Date)

    def __init__(self, title, scrape_dt):
        self.title = title
        self.scrape_dt = scrape_dt

    def __repr__(self):
        return "<Event(title=%s, scrape_dt=%s)>" % (self.title, self.scrape_dt)


try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    event_list = getEvents()
    new_events = getNewEvents(session, event_list)
    if new_events != []:
        sendNotification('New Events:\n' + '\n'.join(new_events))
    old_events = delOldEvents(session, event_list)
    if old_events != []:
        sendNotification('Removed Events:\n' + '\n'.join(old_events))
except Exception as e:
    sendNotification(f'ERROR: {e}')
finally:
    session.close()
