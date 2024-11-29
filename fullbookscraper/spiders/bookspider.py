import scrapy
import random
from fullbookscraper.items import BookItem

from urllib.parse import urlencode

# API_KEY = '567c03fa-5e12-4f97-a1d6-31d98ed80ff9'

# def get_scrapeops_url(url):
#     payload = {'api_key': API_KEY, 'url': url}
#     proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
#     return proxy_url

class BookspiderSpider(scrapy.Spider):
    name = "bookspider"
    allowed_domains = ["books.toscrape.com", "proxy.scrapeops.io"]
    start_urls = ["https://books.toscrape.com"]

    custom_settings = {
        'FEEDS' : {
            'overwritebooksdata.json': {'format': 'json', 'overwrite': True},
        }
    }

    # def start_requests(self):
    #     yield scrapy.Request(url=get_scrapeops_url(self.start_urls[0]), callback = self.parse)


    def parse(self, response):
        # Get all the books details from the webpage 
        books = response.css('article.product_pod')

        for book in books:
            # Get each individual books detail page URL
            relative_url = book.css('article.product_pod h3 a::attr(href)').get()

            if relative_url.startswith('catalogue'):
                # Concatenate url 
                book_detail_page_url = 'https://books.toscrape.com/' + relative_url
            else:
                # Without 'catalogue' in the URL
                book_detail_page_url = 'https://books.toscrape.com/catalogue/' + relative_url
            
            # yield response.follow(book_detail_page_url, callback = self.parse_book_page, headers={"User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list)-1)]} )
            # yield response.follow(url=get_scrapeops_url(book_detail_page_url), callback = self.parse_book_page)
            yield response.follow(book_detail_page_url, callback = self.parse_book_page)

        # Get next page URLs
        next_page = response.css('li.next a::attr(href)').get()

        # Validation for pagination
        if next_page is not None:
            # Check if URL contains 'catalogue'
            if next_page.startswith('catalogue'):
                # Concatenate url 
                next_page_url = 'https://books.toscrape.com/' + next_page
            else:
                # Without 'catalogue' in the URL
                next_page_url = 'https://books.toscrape.com/catalogue/' + next_page
            
            # yield response.follow(next_page_url, callback = self.parse, headers={"User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list)-1)]} )
            # yield response.follow(url=get_scrapeops_url(next_page_url), callback = self.parse)
            yield response.follow(next_page_url, callback = self.parse)

    def parse_book_page(self, response):

        # Extract table data
        table_rows = response.css("table tr")

        book_item = BookItem()
        
        book_item['url'] = response.url,
        book_item['title'] = response.xpath("//div[contains(@class,'product_main')]//h1/text()").get(),
        book_item['product_type'] = table_rows[1].css("td ::text").get(),
        book_item['price_excl_tax'] = table_rows[2].css("td ::text").get(),
        book_item['price_incl_tax'] = table_rows[3].css("td ::text").get(),
        book_item['tax'] = table_rows[4].css("td ::text").get(),
        book_item['availability'] = table_rows[5].css("td ::text").get(),
        book_item['num_reviews'] = table_rows[6].css("td ::text").get(),
        book_item['stars'] = response.xpath("//div[contains(@class, 'product_main')]//p[contains(@class, 'star-rating')]/@class").get(),
        book_item['description'] = response.xpath("//div[@id='product_description']/following-sibling::p/text()").get(),
        book_item['price'] = response.css('.product_main .price_color::text').get(),

        yield book_item