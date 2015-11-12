#! env/bin/python
# coding: utf-8
import sys
import os
import json
import requests
from bs4 import BeautifulSoup as BSoup



class Crawler:

    url = u'http://www.koohbaad.ir/'

    def __init__(self):
        request = self.requester(self.url)
        if not request:
            raise 'Please try agin'
        site = BSoup(request.text.strip(), 'html.parser')
        self.site_map = self.__get_products(site)


    def requester(self, url):
        if type(url) != unicode:
            return
        print '--------- wait for requesting %s ----------->>' % url
        request = requests.get(url,  timeout=(3.05, 27))
        return request
        # try:

        # except requests.exceptions.Timeout:
        #     print 'shit time out! but we try again'
        #     self.requester(url)
        # except requests.exceptions.RequestException:
        #     return
        # self.requester(url)

    def __categories_link_update(self, site):
        category_class = '.k2CMSListMenuLI'
        c1_category_class = '.k3CMSListMenuLink'
        categories = site.select(category_class)
        response = list()
        for index, category in enumerate(categories):
            in_load = dict()
            if index > 2:
                break
            in_load.update({'name': category.a.text,
                            'c1_categories': []})
            #print '#' * 20, 'category %d' %index, category.a.text , '#' * 20
            print len(category.ul.select(c1_category_class)), '-' * 50
            for sub in category.ul.select(c1_category_class):
                # print '*' * 20, 'c1-category--', sub.text , '*' * 20
                sub_link = self.__normalize_links(sub.get('href'))
                c1_category = {
                    'name': sub.text,
                    'link': sub_link,
                    'c2_categories': []
                }
                c1_req = self.requester(sub_link)
                if not c1_req:
                    continue
                c1_page = BSoup(c1_req.text.strip(), 'html.parser')
                sub2_links = c1_page.select('#sideMenu')[0].find_all('a')
                for sub2 in sub2_links:
                    # print '%' * 20, 'c2-category--', sub2.text , '%' * 20
                    sub2_link = self.__normalize_links(sub2.get('href'))
                    c2_category = {
                    'name': sub2.text,
                    'link': sub2_link
                    }
                    c1_category['c2_categories'].append(c2_category)
                in_load['c1_categories'].append(c1_category)
            response.append(in_load)
        print '#' * 200
        print '\n----------finished categories tree------------------\n'
        print '#' * 200
        return response

    def __normalize_links(self, href):
        if 'http' in href:
            return
        if href.startswith('#') or '.' in href:
            return
        if href.startswith('/'):
            href = href.replace('/', '', 1)
        href = self.url + href
        return href

    def __normalize_image_link(self, src):
        pass

    def __normalize_price(self, price):
        price = price.replace(',', '')
        return int(price)

    def __get_pages_link(self, page):
        page_links = page.select('.UnselectedPage')
        pages = [page]
        if not page_links:
            return pages
        for link in page_links:
           pages.append(self.__normalize_links(link.get('href')))
        return pages

    def __product_getter(self, pages):
        items = []
        for index, link in enumerate(pages):
            req = self.requester(link)
            if not req:
                continue
            page = BSoup(req.text.strip(), 'html.parser')
            for item in page.select('.ProductItem'):
                discount = 0
                discount_link = item.a.select('.ProductDiscountedPrice')
                if discount_link:
                    discount = self.__normalize_price(discount_link[0].text)
                product_link = self.__normalize_links(item.a.get('href')),
                get_details = self.__get_image_and_description(product_link)
                image = None
                description = None
                if get_details:
                    image = get_details[0]
                    description = get_details[1]
                product = dict(
                    name = item.a.h4.text,
                    link = product_link,
                    price = self.__normalize_price(
                        item.a.select('.ProductPrice')[0].span.text),
                    discount = discount,
                    image = image,
                    description = description
                )
                items.append(product)
                print '#' * 20, 'Got product --> %s' % product['name'], '#' * 20
        return items

    def __get_image_and_description(self, link):
        req = self.requester(link)
        print req, '&&' * 20
        page = BSoup(req.text, 'html.parser')
        image = self.__normalize_links(page.select('.Image')[0].get('src'))
        print image, '<----------->'
        tab_panel = page.select('.TabPanel')[0]
        tab_panel_1 = tab_panel.select('.tabs-1')[0].p.text
        tab_panel_2 = tab_panel.select(
            '.tabs-1')[1].select(
                '.detail-overview-property')[0].text
        description = tab_panel_1 + '/**/' + tab_panel_2
        return image, description

    def __get_products(self, site):
        site_map = self.__categories_link_update(site)
        len_products = 0
        for category in site_map:
            for c1 in category['c1_categories']:
                for c2 in c1['c2_categories']:
                    req = self.requester(c2['link'])
                    if not req:
                        continue
                    product_page = BSoup(
                        req.text.strip(),
                        'html.parser')
                    pages = self.__get_pages_link(product_page)
                    products = self.__product_getter(pages)
                    c2.update({
                        'products': products
                    })
                    len_products += len(c2['products'])
                    print ' product found %d product ' % len_products
        return site_map

    @property
    def get_export(self):
        with open("map.json", "a") as f:
            f.write(json.dumps(self.site_map))
            f.close()
        print '#%' * 200
        print '\n Crwaling has been finished \n'
        print '#%' * 200

    # def __pages_update(self):
    #     for link in self.links:
    #         page = BSoup(requests.get(link).text, 'html.parser')
    #         self.products_page.append(page)
    #         self.__links_update(page)






if __name__ == '__main__':
    crawler = Crawler().get_export
