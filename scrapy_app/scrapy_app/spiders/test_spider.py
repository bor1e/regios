import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domain = ["toscrape.com"]
    start_urls = [
            'http://quotes.toscrape.com',
        ]
    #for url in urls:
    #   yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.log('visited: ' + response.url)
        for quote in response.css('div.quote'):
            item = {
                'author_name': quote.css('small.author::text').extract_first(),
                'text': quote.css('span.text::text').extract_first(),
                'tags': quote.css('a.tag::text').extract_first(),
            }
            yield item
        next_page_url = response.css('li.next > a::attr(href)').extract_first()
        next_page_url = response.urljoin(next_page_url)
        yield scrapy.Request(url=next_page_url, callback=self.parse)

