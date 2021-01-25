# phpBB Forum Scraper

Python-based web scraper for phpBB forums. Project can be used as a template for building your own
custom Scrapy spiders or for one-off crawls on designated forums. Please keep in mind that aggressive crawls
can produce significant strain on web servers, so please throttle your request rates.


## Requirements: 

1. Python web scraping library, [Scrapy](http://scrapy.org/).   
2. Python HTML/XML parsing library, [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).
3. Excel output extension for Scrapy, [Scrapy-xlsx](https://pypi.org/project/scrapy-xlsx/)


## Scraper Output

The phpBB.py spider scrapes the following information from forum posts:
1. Username
2. Post Text
3. Quoted Text

If you need additional data scraped, you will have to create additional spiders or edit the existing spider.

The output is written to an Excel spreadsheet with Username, Post, and Quote as the first three column headers and corresponding data below.

## Running the Scraper:
```bash
cd phpBB_scraper/
scrapy crawl phpBB [-a start_urls='start_url0,start_url1,...'] [-a allowed_domains='allowed_domain0,allowed_domain1,...'] [-a forums='forum0,forum1,...'] [-a threads='thread0,thread1,...'] [-a login_url='login_url'] [-a username='username'] [-a password='password']
```
NOTE: Please adjust `settings.py` to throttle your requests.

## Example:
```bash
cd phpBB_scraper
scrapy crawl phpBB -a start_urls='https://talkabouttennis2.com' -a allowed_domains='talkabouttennis2.com' -a forums='f=3,f=5' -a threads='f=5&t=70' -o posts
```
This will scrape only the thread in https://talkabouttennis2.com with thread ID 70 in the forum with ID 5, which is a subforum of the forum with ID 3. You must provide all intermediate forums for the scraper to be able to find your subforum.

## Warning:

Edits were made to the original repository going off of a forum using phpBB 3.3.2, as some of the code was out of date. Any change to phpBB may make it so this code does not work.