import scrapy
import time
import datetime
import re

class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['wildberries.ru']
    start_urls = ['https://www.wildberries.ru/catalog/obuv/zhenskaya/galoshi']

    def parse(self, response):
        urls = response.css('div#body-layout > div.left-bg > div.trunkOld > div#catalog > div#catalog-content > ' + 
        'div.catalog_main_table > div.dtList > span > span > span > a.ref_goods_n_p::attr(href)').extract()
        for url in urls:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, callback=self.parse_details)
        #follow pagination link
        next_page_url = response.css('div#body-layout > div.left-bg > div.trunkOld > div#catalog >' + 
        'div#catalog-content > div.pager > div.pageToInsert > a.next::attr(href)').extract_first()

        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse)
    
    def parse_details(self, response):
        
        PATH_TO_DESCRIPTION = 'div#body-layout > div.left-bg > div.trunkOld > div#container > div.product-content > div.card-row > div.card-left2 > div.card-add-info > div.j-collapsable-card-add-info > div.j-add-info-section'
        PATH_TO_PRICE = 'div#body-layout > div.left-bg > div.trunkOld > div#container > div.product-content > div.card-row > div.card-right > div.j-price > div#cost > div.inner-price'
        
        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        def get_price(query):
            p = response.css(query).get(default='').strip()
            if p:
                p = re.findall('\d+', p)
                return float(''.join(p))
            return False

        def get_discount(query):
            d = response.css(query).get(default='').strip()
            if d:
                d = re.findall('\d+', d)
                return ''.join(d) + '%'
            return False

        def get_in_stock(query):
            s = response.css(query).extract()
            label = []
            for item in s:
                label.append(item)
            for item in label:
                if item == ('j-size  disabled j-sold-out'):
                    continue
                else:
                    return True
            return False

        def get_image(query):
            img_url = response.css(query).extract()
            img_url = ''.join(img_url)
            return response.urljoin(img_url)

        yield{
            'url': response.css('head > link::attr(href)').extract()[1],
            'article': response.css('head > link::attr(href)').extract()[1].split('/')[-2],
            'timestamp': datetime.datetime.now().timestamp(),
            'title': extract_with_css('div#body-layout > div.left-bg > div.trunkOld > div#container > ' + 
                    'div.product-content > div.card-row > div.card-right > div.good-header > ' + 
                    'div.brand-and-name > span.name::text'),
            'brand': extract_with_css('div#body-layout > div.left-bg > div.trunkOld > div#container > ' + 
                    'div.product-content > div.card-row > div.card-right > div.good-header > ' +
                    'div.brand-and-name > span.brand::text'),
            'price_data': {'current': get_price(PATH_TO_PRICE + ' > div.add-discount > div.add-discount-info > ' + 
                                    'div.add-discount-text > span.add-discount-text-price::text'),
                            'original': get_price(PATH_TO_PRICE + ' > div.price > ins > span.old-price > del.c-text-base::text'),
                            'discount': get_discount(PATH_TO_PRICE + ' > div.add-discount > div.j-promo-tooltip-content > ' + 
                                    'div.discount-tooltipster-content > p > span::text')},
            'in_stock': get_in_stock('div#body-layout > div.left-bg > div.trunkOld > div#container > div.product-content > ' + 
                    'div.card-row > div.card-right > div.pp-sizes > div.j-size-list > label.j-size::attr(class)'),
            'assets': get_image('div#body-layout > div.left-bg > div.trunkOld > ' + 
                    'div#container > div.product-content > div.card-row > div.card-left > ' + 
                    'div#photo > a::attr(href)'), 
            'metadata': {'description': extract_with_css(PATH_TO_DESCRIPTION + ' > div.j-description > p::text'),
                            'structure': response.css(PATH_TO_DESCRIPTION + ' > p.composition > span::text').extract()[1].strip(),
                            'fullness_of_shoes': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[2].strip(),
                            'insole_material': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[3].strip(),
                            'shoe_material': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[4].strip(),
                            'heel_height': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[5].strip(),
                            'tackle': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[6].strip(),
                            'gender': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[7].strip(),
                            'season': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[8].strip(),
                            'brand_country': response.css(PATH_TO_DESCRIPTION + ' div.params > div.pp > span::text').extract()[9].strip(),}                
        }