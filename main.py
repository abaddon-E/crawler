#! env/bin/python
# coding: utf-8
import sys
import os
import json
import requests
import xlsxwriter
from bs4 import BeautifulSoup as BSoup



class Crawler:

    url = 'http://www.koohbaad.ir/'

    def __init__(self):
        request = requests.get(self.url).text.strip()
        site = BSoup(request, 'html.parser')
        # self.products_pages = []
        self.sub_categories_links = dict()
        self.__categories_link_update(site)
        self.site_map = self.__categories_link_update(site)
        self.__get_products()


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
            for sub in category.ul.select(c1_category_class):
                sub_link = self.__normalize_links(sub.get('href'))
                c1_category = {
                    'name': sub.text,
                    'link': sub_link,
                    'c2_categories': []
                }
                c1_req = requests.get(sub_link).text.strip()
                c1_page = BSoup(c1_req, 'html.parser')
                sub2_links = c1_page.select('#sideMenu')[0].find_all('a')
                for sub2 in sub2_links:
                    sub2_link = self.__normalize_links(sub2.get('href'))
                    c2_category = {
                    'name': sub2.text,
                    'link': sub2_link
                    }
                    c1_category['c2_categories'].append(c2_category)
                    print '$&' * 100
                    print c1_category
                in_load['c1_categories'].append(c1_category)
            response.append(in_load)
        # with open("map.json", "a") as f:
        #     f.write(json.dumps(response))
        #     f.close()
        # print '^' * 200
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
        print pages
        for index, link in enumerate(pages):
            try:
                print link, '%' * 50
                req = requests.get(link)
            except:
                continue
            print req, '%' * 30
            page = BSoup(req.text.strip(), 'html.parser')
            items = []
            for item in page.select('.ProductItem'):
                product = dict(
                    name = item.a.h4.text,
                    link = self.__normalize_links(item.a.get('href')),
                    price = self.__normalize_price(
                        item.a.select('.ProductPrice')[0].span.text)
                )
                items.append(product)
            return items


    def __get_products(self):
        for category in self.site_map:
            for c1 in category['c1_categories']:
                for c2 in c1['c2_categories']:
                    print c2
                    product_page = BSoup(
                        requests.get(c2['link']).text.strip(),
                        'html.parser')
                    pages = self.__get_pages_link(product_page)
                    products = self.__product_getter(pages)
                    c2.update({
                        'products': products
                    })
                    print c2
                    print '%' * 200


    # def __pages_update(self):
    #     for link in self.links:
    #         page = BSoup(requests.get(link).text, 'html.parser')
    #         self.products_page.append(page)
    #         self.__links_update(page)






if __name__ == '__main__':
    crawler = Crawler()
