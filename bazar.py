#!/usr/bin/env python
#-*- coding: utf-8 -*-
import requests
import bs4
from pprint import pprint
from datetime import datetime, timedelta
import time
from random import randint
import os
import urllib
import re
import logging
import logging.handlers
from mongoengine import *
from optparse import OptionParser

connect('appstore')
# connect('cafe', host='mongodb://localhost:28017/cafe')
root_url = 'https://cafebazaar.ir'
image_path = './../project/media/static/images/applications/'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ApplicationsUpdate(EmbeddedDocument):
    version = StringField()
    active_install_str = StringField()
    active_install = StringField()
    star_count = StringField()
    stars_count = ListField()
    app_size = StringField()
    app_price = StringField()
    page_html = StringField()
    create_date = DateTimeField(default=datetime.now)

class Applications(Document):
    title = StringField()
    name = StringField()
    market = StringField(default='bazar')
    author_name = StringField()
    author_link = StringField()
    link = StringField()
    lang = BooleanField(default=False)
    purchase = BooleanField(default=False)
    category_name = StringField()
    category_name_en = StringField()
    category_link = StringField()
    deleted_date = DateTimeField()
    wrong_date = DateTimeField()
    last_active_install = LongField()
    last_star_count = LongField()
    last_app_size = LongField()
    last_app_price = LongField()
    create_date = DateTimeField(default=datetime.now)
    last_update = DateTimeField(default=datetime.now)
    images = ListField()
    updates = ListField(EmbeddedDocumentField(ApplicationsUpdate))

class AppsInMarket(Document):
    title = StringField()
    name = StringField()
    author_name = StringField()
    bazar = ReferenceField('Applications')
    myket = ReferenceField('Applications')
    iranapps = ReferenceField('Applications')
    cando = ReferenceField('Applications')
    total_install = LongField()
    total_star_count = LongField()
    categories = ListField()
    last_update = DateTimeField(default=datetime.now)


def get_all_categorie_url():
    response = requests.get(root_url)
    if not len(response.text.strip()) or response.status_code != 200:
        return False

    soup = bs4.BeautifulSoup(response.text)
    excludes = ['new', 'persian', 'non-persian', 'most_installed', 'most_bookmarked', 'trending']
    categoryUrls = []
    for category in soup.select('.cat'):
        category_name = re.findall('cat\/(.*?)\?', str(category.get('href')))
        if category_name and category_name[0] not in excludes:
            categoryUrls.append({category_name[0] : str(root_url) + '/cat/' + category_name[0] + '/part/%s/?l=fa'})

    return categoryUrls

def get_categories_url_by_name(categories_name):
    response = requests.get(root_url)
    if not len(response.text.strip()) or response.status_code != 200:
        return False

    soup = bs4.BeautifulSoup(response.text)
    categoryUrls = []
    for category in soup.select('.cat'):
        category_name = re.findall('cat\/(.*?)\?', str(category.get('href')))
        if category_name and category_name[0] in categories_name :
            categoryUrls.append({category_name[0] : str(root_url) + '/cat/' + category_name[0] + '/part/%s/?l=fa'})

    return categoryUrls

def get_apps_by_category(category_url, category_name=None):
    response = requests.get(category_url)
    if not len(response.text.strip()) or response.status_code != 200:
        return False

    if not category_name :
        urlPars = re.findall('cat\/(.*?)\/part', str(category_url))
        if urlPars and urlPars[0] :
            category_name = urlPars[0]

    soup = bs4.BeautifulSoup(response.text)
    appData = []
    for card in soup.select('.scard'):
        app_lang = 0
        if 'fa-card' in card['class']:
            app_lang = 1

        app_link = card.a.get('href')
        pakage_name = re.findall('app\/(.*?)\?', app_link)

        data = {
            'link' : root_url + app_link,
            'name' : pakage_name[0],
            'category_name_en' : category_name,
            'lang' : app_lang,
            'title' : card.select("span.scard-title")[0].get_text(),
            'author_name' : card.select("span.scard-dev")[0].get_text(),
            'last_update' : str(datetime.now())
        }

        if check_exist_app(data['link']):
            # print bcolors.WARNING + 'App exist : %s' % (data['title']) + bcolors.ENDC
            logger.warning("get_apps_by_category app-exist", extra={'action':data['title']})
        else :
            # print bcolors.OKBLUE + 'App saved : %s' % (data['title']) + bcolors.ENDC
            logger.info("get_apps_by_category app-saved", extra={'action':data['title']})
            app = Applications(**data)
            app.save()

    return True

def check_exist_app(app_url):
    count = Applications.objects(market='bazar', link=app_url).count()
    if count :
        return True

    return False

def save_category(category, category_url):
    pageNumber = 0
    while get_apps_by_category(category_url % (pageNumber)):
        pageNumber += 1
        # print bcolors.OKGREEN + 'Saved page(%s) part(%s)' % (category, pageNumber) + bcolors.ENDC
        logger.info("save_category page-saved", extra={'action':(category, pageNumber)})
        time.sleep(randint(1,5))
        pass

    return True

def save_all_categories(category_urls=None):
    if not category_urls :
        category_urls = get_all_categorie_url()

    if category_urls :
        # print bcolors.WARNING + 'Save %s categories started!' % (len(category_urls)) + bcolors.ENDC
        logger.info("save_all_categories category-start", extra={'action':len(category_urls)})
        befor_save_count = Applications.objects(market='bazar').count()

        for category in category_urls:
            categoryName = category.keys()[0]
            if save_category(categoryName, category[categoryName]) :
                # print bcolors.OKBLUE + 'Category %s saved!' % (categoryName) + bcolors.ENDC
                logger.info("save_all_categories category-saved", extra={'action':categoryName})
                continue
            time.sleep(randint(1,5))

        after_save_count = Applications.objects(market='bazar').count()
        # print bcolors.WARNING + 'Totall apps is %s & %s apps is new' % (befor_save_count, after_save_count - befor_save_count) + bcolors.ENDC
        logger.info("save_all_categories totall-new-app", extra={'action':(after_save_count - befor_save_count)})

        return True

    return False

def update_app(app_url):
    if check_exist_app(app_url) :
        logger.info("update_app started", extra={'action':app_url})

        apps = Applications.objects(market='bazar', link=app_url)
        try:
            response = requests.get(app_url, allow_redirects=True, timeout=5.0)
        except:
            if str(response.status_code).startswith('5') :
                logger.warning("update_app Error 500", extra={'action':apps[0].link})

            elif response.status_code == 404 or not len(response.text.strip()) :
                appData = {
                    'deleted_date' : str(datetime.now())
                }
                apps.update(**appData)
                # print bcolors.FAIL + 'App (%s) Deleted!' % (apps[0].link) + bcolors.ENDC
                logger.warning("update_app deleted", extra={'action':apps[0].link})

            return False

        soup = bs4.BeautifulSoup(response.text)
        if soup.select('.app-detail-panel') :
            appDetail = soup.select('.app-detail-panel')[0]

            rateDetail = soup.select('.rating-line')
            rates = []
            for rate in rateDetail:
                rates.append(en_numbers(rate.select('div')[0].get_text().strip()))

            del rates[0]

            ratingCount = appDetail.select('[itemprop="ratingCount"]')
            if ratingCount :
                ratingCount = ratingCount[0]['content'].strip()
            else :
                ratingCount = 0

            softwareVersion = appDetail.select('[itemprop="softwareVersion"]')
            if softwareVersion :
                softwareVersion = softwareVersion[0].get_text().strip()
            else :
                softwareVersion = 0

            fileSize = appDetail.select('[itemprop="fileSize"]')
            if fileSize :
                fileSize = fileSize[0]['content'].strip()
            else :
                fileSize = 0

            price = appDetail.select('[itemprop="price"]')
            if price :
                price = price[0]['content'].strip()
            else :
                price = 0

            updateData = {
                'version' : softwareVersion,
                # 'active_install_str' : en_numbers(appDetail.select('[itemprop="numdownloads"]')[0].get_text().strip()),
                # 'active_install' : str_to_numbers(en_numbers(appDetail.select('[itemprop="numdownloads"]')[0].get_text().strip())),
                'star_count' : ratingCount,
                'stars_count' : rates,
                'app_size' : fileSize,
                'app_price' : price,
                'page_html' : response.text,
                'create_date' : str(datetime.now())
            }

            active_install_str = 0
            download_icon = appDetail.select('.fa-cloud-download')
            if download_icon :
                download_icon_parent = download_icon[0].find_parent('div')
                if download_icon_parent :
                    active_install_str = download_icon_parent.select('span')[0].get_text().strip()

            updateData['active_install_str'] = en_numbers(active_install_str)
            updateData['active_install'] = str_to_numbers(en_numbers(active_install_str))
            
            apps.update_one(push__updates=updateData)

            appData = {
                'last_active_install' : updateData['active_install'],
                'last_star_count' : updateData['star_count'],
                'last_app_size' : updateData['app_size'],
                'last_app_price' : updateData['app_price'],
                'last_update' : str(datetime.now())
            }

            if 'last_active_install' in apps[0] :
                pre_active_install = apps[0]['last_active_install']
                pre_star_count = apps[0]['last_star_count']
            else :
                pre_active_install = 0
                pre_star_count = 0

            app_price = appDetail.select('.price b')
            if app_price :
                app_price = unicode(app_price[0])
                if app_price.find(u'با پرداخت درون‌برنامه‌ای') :
                    appData['purchase'] = True

            author_name = appDetail.select('span[itemprop="name"]')
            if author_name :
                author_name = author_name[0].get_text().strip()
            else :
                author_name = ''

            category_name = appDetail.select('[itemprop="applicationSubCategory"]')
            if category_name :
                category_name = category_name[0].get_text().strip()
            else :
                category_name = ''

            image_path = get_app_img_path(apps[0].name, updateData['version'])
            save_app_icon(apps[0].name, image_path)
            save_app_qr(apps[0].name, image_path)

            images = soup.select('img.app-screenshot')
            if images :
                app_images = []
                for image in images :
                    if image.attrs['src'] :
                        image_file_name = image.attrs['src'].split('/')[-1]
                        image_file_path = image_path + image_file_name
                        if not os.path.exists(image_file_path):
                            urllib.urlretrieve('http:' + image.attrs['src'], image_file_path)
                            app_images.append(image_file_name)

                if app_images :
                    appData['images'] = app_images


            if 'category_link' not in apps[0] :
                category_link = appDetail.select('[itemprop="applicationSubCategory"]')
                if category_link :
                    category_link = category_link[0].find_parent('a')['href'].strip()
                else :
                    category_link = ''

                appData.update({
                    'author_link' : getattr(appDetail.select('.dev a')[0], 'href', ''),
                    'author_name' : author_name,
                    'category_link' : category_link,
                    'category_name' : category_name
                })

                if appData and appData['category_link']:
                    urlParse = re.findall('cat\/(.*?)\?', str(appData['category_link']))
                    if urlParse and urlParse[0]:
                        appData['category_name_en'] = urlParse[0]

            apps.update(**appData)

            appinmarket = AppsInMarket.objects(name=apps[0].name)
            if appinmarket :
                if 'bazar' in appinmarket[0] :
                    appinmarketData = {
                        'total_install' : (int(appinmarket[0].total_install) - int(pre_active_install)) + int(updateData['active_install']),
                        'total_star_count' : (int(appinmarket[0].total_star_count) - int(pre_star_count)) + int(updateData['star_count']),
                        'last_update' : str(datetime.now())
                    }
                    appinmarket.update(**appinmarketData)
                else :
                    appinmarket[0].categories.append(category_name)
                    appinmarketData = {
                        'bazar' : apps[0],
                        'total_install' : int(appinmarket[0].total_install) + int(updateData['active_install']),
                        'total_star_count' : int(appinmarket[0].total_star_count) + int(updateData['star_count']),
                        'categories' : appinmarket[0].categories,
                        'last_update' : str(datetime.now())
                    }
                    appinmarket.update(**appinmarketData)
            else :
                appinmarketData = {
                    'bazar' : apps[0],
                    'title' : apps[0].title,
                    'name' : apps[0].name,
                    'author_name' : author_name,
                    'total_install' : int(updateData['active_install']),
                    'total_star_count' : int(updateData['star_count']),
                    'categories' : [category_name],
                    'last_update' : str(datetime.now())
                }
                appinmarket = AppsInMarket(**appinmarketData)
                appinmarket.save()

            return True

        else :
            appData = {
                'wrong_date' : str(datetime.now())
            }
            apps.update(**appData)
            # print bcolors.FAIL + 'App (%s) Wrong Data!' % (apps[0].link) + bcolors.ENDC
            logger.warning("update_app wrong-data", extra={'action':apps[0].link})

    return False

def fix_bug_app_cat():
    apps = Applications.objects(market='bazar', category_name_en='new', category_link__exists=True, deleted_date__exists=False, wrong_date__exists=False)
    for app in apps:
        print app['link']

        if check_exist_app(app['link']) :
            response = requests.get(app['link'], allow_redirects=True, timeout=5.0)

            if str(response.status_code).startswith('5') :
                print "update_app Error 500"

            elif response.status_code == 404 or not len(response.text.strip()) :
                appData = {
                    'deleted_date' : str(datetime.now())
                }
                apps.update(**appData)

                print "update_app deleted"

            else :
                soup = bs4.BeautifulSoup(response.text)
                if soup.select('.app-detail-panel') :
                    appDetail = soup.select('.app-detail-panel')[0]

                    category = appDetail.select('[itemprop="applicationSubCategory"]')
                    if category :
                        category_link = category[0].find_parent('a')['href'].strip()
                        category_name = category[0].get_text().strip()
                    else :
                        category_name = ''
                        category_link = ''

                    if category_link:
                        urlParse = re.findall('cat\/(.*?)\?', str(category_link))
                        if urlParse and urlParse[0]:
                            category_name_en = urlParse[0]
                    
                    updateData = {
                        'category_name' : category_name,
                        'category_name_en' : category_name_en,
                        'category_link' : category_link
                    }
                    app.update(**updateData)


def str_to_numbers(number):
    num = re.findall(r'\d+', number.replace('کمتر از', ''))
    
    if number.find('+'):
        num = int(num[0]) + 1
    elif number.find('-') or number.find('کمتر از'):
        num = int(num[0]) - 1

    return num

def en_numbers(number):
    number = unicode(number)
    number = number.encode('utf8')
    number = number.replace("٬", '').replace('کمتر از', '-').strip()
    return persian_num_to_english(number)

def persian_num_to_english(persian_num):
    l2p = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    p2l = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    persian_num = str(persian_num)
    place = 0
    for integer in l2p:
        persian_num = persian_num.replace(integer, p2l[place])
        place += 1
    return persian_num

def update_new_apps():
    start = 0
    limit = 500

    total_apps = Applications.objects(market='bazar', category_link__exists=False, deleted_date__exists=False, wrong_date__exists=False).count()
    total = int(total_apps / limit)
    
    if not total or total < 1 :
        total = 1

    # print bcolors.WARNING + 'Total app to update is %s in %s' % (total_apps, total) + bcolors.ENDC
    logger.info("update_new_apps total-apps", extra={'action':total_apps})

    for i in range(start, total):
        # print bcolors.WARNING + 'Start %s' % (start) + bcolors.ENDC
        logger.info("update_new_apps start", extra={'action':start})
        apps = Applications.objects[start:limit](market='bazar', category_link__exists=False, deleted_date__exists=False, wrong_date__exists=False).only("link", "title")
        for app in apps:
            logger.info("update_new_apps update start", extra={'action':app.link})
            if update_app(app.link):
                # print bcolors.OKGREEN + 'App (%s) updated!' % (app.link) + bcolors.ENDC
                logger.info("update_new_apps updated", extra={'action':app.link})
                time.sleep(randint(2,7))
                continue
            else :
                # print bcolors.WARNING + 'App (%s) NOT updated!' % (app.link) + bcolors.ENDC
                logger.warning("update_new_apps not-updated", extra={'action':app.link})

    return False

def update_all_apps(date=None):
    start = 0
    limit = 500

    if not date :
        date = datetime.today().date()

    total_apps = Applications.objects(market='bazar', deleted_date__exists=False, wrong_date__exists=False, last_update__lte=str(date)).count()
    total = int(total_apps / limit)
    
    if not total or total < 1 :
        total = 1

    # print bcolors.WARNING + 'Total app to update is %s' % (total_apps) + bcolors.ENDC
    logger.info("update_all_apps total-app", extra={'action':total_apps})

    for i in range(start, total):
        # print bcolors.WARNING + 'Start %s' % (start) + bcolors.ENDC
        logger.info("update_all_apps start", extra={'action':start})
        apps = Applications.objects[start:limit](market='bazar', deleted_date__exists=False, wrong_date__exists=False, last_update__lte=str(date)).only("link", "title")
        for app in apps:
            if update_app(app.link):
                # print bcolors.OKGREEN + 'App (%s) updated!' % (app.link) + bcolors.ENDC
                logger.info("update_all_apps updated", extra={'action':app.link})
                time.sleep(randint(2,7))
                continue
            else :
                # print bcolors.WARNING + 'App (%s) NOT updated!' % (app.link) + bcolors.ENDC
                logger.warning("update_all_apps not-updated", extra={'action':app.link})

    return False


def get_app_img_path(app_name, app_version):
    app_image_path = image_path + app_name + "/" + 'bazar' + "/" + app_version + "/"
    if not os.path.exists(app_image_path):
        os.makedirs(app_image_path, 0777)
        os.chmod(image_path + app_name, 0777)
        os.chmod(app_image_path, 0777)

    return app_image_path
    

def save_app_icon(app_name, app_img_path):
    app_icon_path = app_img_path + "icon.png"
    if not os.path.exists(app_icon_path):
        urllib.urlretrieve("http://s.cafebazaar.ir/1/icons/" + app_name + "_128x128.png", app_icon_path)

    return True


def save_app_qr(app_name, app_img_path):
    app_qr_path = app_img_path + "qr_code.png"
    if not os.path.exists(app_qr_path):
        urllib.urlretrieve("https://api.qrserver.com/v1/create-qr-code/?size=170x170&data=https://cafebazaar.ir/app/?id=" + app_name + "%26ref=web_QR", app_qr_path)
    
    return True


def logger_init(filename='bazar.log'):
    logger = logging.getLogger('BazarCrawler')
    if not len(logger.handlers):
        log_file_name = '/home/appyom/logs/%s' % (filename)
        hdlr = logging.handlers.RotatingFileHandler(
            log_file_name,
            maxBytes=200000,
            backupCount=10)
        #hdlr = logging.StreamHandler()
        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(action)s - %(message)s')
        # add formatter to ch
        hdlr.setFormatter(formatter)
        memoryhandler = logging.handlers.MemoryHandler(1024*1, logging.DEBUG, hdlr)
        logger.addHandler(memoryhandler)
        logger.setLevel(logging.DEBUG)
    return logger

logger = logger_init()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-a", "--apps", dest="apps")
    parser.add_option("-c", "--cats", dest="cats")
    parser.add_option("-u", "--update", dest="update")
    parser.add_option("-f", "--fix", dest="fix")
 
    (options, args) = parser.parse_args()
    apps = options.apps
    cats = options.cats
    update = options.update
    fix = options.fix

    logger = logger_init('bazar-crawler.log')
    run_times = 1

    if apps :
        # print bcolors.OKGREEN + 'Update Apps' + bcolors.ENDC
        try:
            logger.info("Applications Update", extra={'action':'Started %s' % run_times})
            update_new_apps()
            
        except:
        # except IOError:
            if run_times < 20 :
                run_times += 1
                logger.warning("Applications Update", extra={'action':'Reloaded %s' % run_times})
                update_new_apps()
            else :
                logger.error("Applications Update", extra={'action':'Stpped %s' % run_times})

            pass
    
    if cats :
        # print bcolors.OKGREEN + 'Update Category' + bcolors.ENDC
        try:
            logger.info("Update Category", extra={'action':'Started %s' % run_times})
            save_all_categories(get_categories_url_by_name('new'))

        except:
        # except IOError:
            if run_times < 20 :
                run_times += 1
                logger.warning("Update Category", extra={'action':'Reloaded %s' % run_times})
                save_all_categories(get_categories_url_by_name('new'))
            else :
                logger.error("Update Category", extra={'action':'Stpped %s' % run_times})

            pass

    if update : 
        try:
            datetime.strptime(update, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")

        # print bcolors.OKGREEN + 'Update All Apps' + bcolors.ENDC
        try:
            logger.info("Update All Apps", extra={'action':'%s Started %s' % (update, run_times)})
            # date = datetime.now() - timedelta(days=2)
            # date = '2015-07-04 00:00:00'
            update_all_apps(update)

        except:
        # except IOError:
            if run_times < 20 :
                run_times += 1
                logger.warning("Update All Apps", extra={'action':'%s Reloaded %s' % (update, run_times)})
                update_all_apps(update)
            else :
                logger.error("Update All Apps", extra={'action':'%s Stpped %s' % (update, run_times)})

            pass

    if fix : 
        try:
            fix_bug_app_cat()
        except:
            fix_bug_app_cat()