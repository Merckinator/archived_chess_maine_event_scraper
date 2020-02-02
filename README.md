# chess_maine_event_scraper
A Python script that scrapes the events from the chessmaine.net website and notifies a Discord channel of additions/deletions.

It is currently scheduled to run at half-past every hour via Heroku's Scheduler. It uses Heroku's postgres database and the Python ORM 'sqlalchemy' to store the list of events and compare to the scraped list.
