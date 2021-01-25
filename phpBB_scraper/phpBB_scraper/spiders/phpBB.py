# -*- coding: utf-8 -*-
import re
import urllib.parse
import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Request

#THREADS = {'f=5&t=70'}

#FORUMS = {'f=3', 'f=5'}

class PhpbbSpider(scrapy.Spider):
    
    name = 'phpBB'
    username_xpath = '//p[contains(@class, "author")]//a[contains(@class, "username")]//text()'
    post_text_xpath = '//div[@class="postbody"]//div[@class="content"]'

    def __init__(self, forums=None, threads=None, allowed_domains=None, forum_login=False, 
        username='', password='', login_url='', start_urls=None, posts_per_page=15, *args, **kwargs):
        self.forums = forums.split(',') if forums else []
        self.threads= threads.split(',') if threads else []
        self.allowed_domains = allowed_domains.split(',') if allowed_domains else ['']
        self.forum_login = forum_login
        self.posts_per_page = posts_per_page
        self.start_urls = []
        if self.forum_login:
            self.username = username
            self.password = password
            self.login_url = login_url
            self.start_urls.append(login_url)
        if start_urls:
            self.start_urls+= start_urls.split(',')
        else:
            self.start_urls.append('')

        super(PhpbbSpider, self).__init__(*args, **kwargs)


    def parse(self, response):
        # LOGIN TO PHPBB BOARD AND CALL AFTER_LOGIN
        if self.forum_login:
            formxpath = '//*[contains(@action, "login")]'
            formdata = {'username': self.username, 'password': self.password}
            form_request = scrapy.FormRequest.from_response(
                    response,
                    formdata=formdata,
                    formxpath=formxpath,
                    callback=self.after_login,
                    dont_click=False
            )
            yield form_request
        else:
            # REQUEST SUB-FORUM TITLE LINKS
            links = response.xpath('//a[@class="forumtitle"]/@href').extract()
            for link in links:
                if link.split('?')[1] in self.forums or not self.forums:
                    yield scrapy.Request(response.urljoin(link), callback=self.parse_topics)

    def after_login(self, response):
        # CHECK LOGIN SUCCESS BEFORE MAKING REQUESTS
        if b'authentication failed' in response.body:
            self.logger.error('Login failed.')
            return
        else:
            # REQUEST SUB-FORUM TITLE LINKS
            links = response.xpath('//a[@class="forumtitle"]/@href').extract()
            for link in links:
                if link.split('?')[1] in self.forums or not self.forums:
                    yield scrapy.Request(response.urljoin(link), callback=self.parse_topics)

    def parse_topics(self, response):
        # REQUEST TOPIC TITLE LINKS
        links = response.xpath('//a[@class="topictitle"]/@href').extract()
        for link in links:
            if link.split('?')[1] in self.threads or not self.threads:
                yield scrapy.Request(response.urljoin(link), callback=self.parse_posts)
        
        # IF NEXT PAGE EXISTS, FOLLOW
        next_link = response.xpath('//li[@class="next"]//a[@rel="next"]/@href').extract_first()
        if next_link:
            yield scrapy.Request(response.urljoin(next_link), callback=self.parse_topics)   

        subforums = response.xpath('//a[@class="forumtitle"]/@href').extract()
        for subforum in subforums:
            if subforum.split('?')[1] in self.forums or not self.forums:
                yield scrapy.Request(response.urljoin(subforum), callback=self.parse_topics)
    
    def clean_quote(self, string):
        # CLEAN HTML TAGS FROM POST TEXT, MARK QUOTES
        soup = BeautifulSoup(string, 'lxml')
        block_quotes = soup.find_all('blockquote')
        for i, quote in enumerate(block_quotes):
            block_quotes[i] = '<quote-%s>=%s' % (str(i + 1), quote.get_text())
        return ''.join(block_quotes).strip()
    
    def clean_text(self, string):
        # CLEAN HTML TAGS FROM POST TEXT, MARK REPLIES TO QUOTES
        tags = ['blockquote']
        soup = BeautifulSoup(string, 'lxml')
        for tag in tags:
            for i, item in enumerate(soup.find_all(tag)):
                item.replaceWith('<reply-%s>=' % str(i + 1))
        return re.sub(r' +', r' ', soup.get_text()).strip()
      
    def parse_posts(self, response):
        # COLLECT FORUM POST DATA
        usernames = response.xpath(self.username_xpath).extract()
        n = len(usernames)
        if n > 0:
            post_texts = response.xpath(self.post_text_xpath).extract() or (n * [''])
            post_quotes = [self.clean_quote(s) for s in post_texts]
            post_texts = [self.clean_text(s) for s in post_texts]

            # YIELD POST DATA
            for i in range(n):
                yield {'Username': str(usernames[i]).strip(), 'Post': post_texts[i], 
                'Quote': post_quotes[i]}

        # This gets you the url but without the forum (not sure why that's not included)
        my_page = urllib.parse.urlparse(response.xpath('//link[@rel="canonical"]/@href').extract_first())
        # But this gets the forum in any case
        forum = urllib.parse.urlparse(response.xpath('//a[@class="left-box arrow-left"]/@href').extract_first()).query
        query = my_page.query.split('&')
        
        # these should be all the links to other pages of the thread
        page_links = response.xpath('//a[@class="button"]//@href').extract()
        if 'start' in query[-1]:
            my_page_start = int(query[-1].split('=')[1])
            prospective_req = f'.{my_page.path}?{forum}&{query[0]}&start={my_page_start + self.posts_per_page}'
        else:
            prospective_req = f'.{my_page.path}?{forum}&{query[0]}&start={self.posts_per_page}'
        if prospective_req in page_links:
            yield scrapy.Request(response.urljoin(prospective_req), callback=self.parse_posts)
