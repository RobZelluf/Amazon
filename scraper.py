#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Written as part of https://www.scrapehero.com/how-to-scrape-amazon-product-reviews-using-python/
from lxml import html
import json
import csv
import requests
import json,re
from dateutil import parser as dateparser
from time import sleep
import random
import numpy as np
import logging
import os

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

DIR = "data/"
filename = "smartplugs1130-5.csv"
file = DIR + filename

save_int = 5
attempts = 3

def ParseReviews(asin):
    # Added Retrying
    for i in range(attempts):
        try:
            #This script has only been tested with Amazon.com
            amazon_url  = 'http://www.amazon.com/dp/'+asin
            # Add some recent user agent to prevent amazon from blocking the request
            # Find some chrome user agent strings  here https://udger.com/resources/ua-list/browser-detail?browser=Chrome
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
            page = requests.get(amazon_url ,headers = headers)
            page_response = page.text
            if "To discuss automated access to Amazon data please contact" in page_response:
                if i < 3:
                    print("Amazon detected scraping, retrying again in 15 minutes.")
                    sleep(60*15)
                else:
                    print("Amazon detected scraping, giving up.. :(")
                    exit()

            parser = html.fromstring(page_response)
            XPATH_AGGREGATE = '//span[@id="acrCustomerReviewText"]'
            XPATH_REVIEW_SECTION_1 = '//div[contains(@id,"reviews-summary")]'
            XPATH_REVIEW_SECTION_2 = '//div[@data-hook="review"]'

            XPATH_AGGREGATE_RATING = '//table[@id="histogramTable"]//tr'
            XPATH_PRODUCT_NAME = '//h1//span[@id="productTitle"]//text()'
            XPATH_PRODUCT_PRICE  = '//span[@id="priceblock_ourprice"]/text()'

            raw_product_price = parser.xpath(XPATH_PRODUCT_PRICE)
            product_price = ''.join(raw_product_price).replace(',','')

            raw_product_name = parser.xpath(XPATH_PRODUCT_NAME)
            product_name = ''.join(raw_product_name).strip()
            total_ratings  = parser.xpath(XPATH_AGGREGATE_RATING)
            reviews = parser.xpath(XPATH_REVIEW_SECTION_1)
            if not reviews:
                reviews = parser.xpath(XPATH_REVIEW_SECTION_2)
            ratings_dict = {}
            reviews_list = []

            if not reviews:
                raise ValueError('unable to find reviews in page')

            #grabing the rating  section in product page
            for ratings in total_ratings:
                extracted_rating = ratings.xpath('./td//a//text()')
                if extracted_rating:
                    rating_key = extracted_rating[0]
                    raw_raing_value = extracted_rating[1]
                    rating_value = raw_raing_value
                    if rating_key:
                        ratings_dict.update({rating_key:rating_value})

            #Parsing individual reviews
            n = 0
            while True:
                n += 1
                sleep(np.random.random() + 0.3)
                review_url = 'https://www.amazon.com/product-reviews/'+asin+'/?pageNumber='+str(n)
                page = requests.get(review_url,headers = headers)
                page_response = page.text
                parser = html.fromstring(page_response)
                reviews = parser.xpath(XPATH_REVIEW_SECTION_1)
                if not reviews:
                    reviews = parser.xpath(XPATH_REVIEW_SECTION_2)
                    if not reviews:
                        break
                XPATH_REVIEW_SECTION_2 = '//div[@data-hook="review"]'
                for review in reviews:
                    XPATH_RATING  = './/i[@data-hook="review-star-rating"]//text()'
                    XPATH_REVIEW_HEADER = './/a[@data-hook="review-title"]//text()'
                    XPATH_REVIEW_POSTED_DATE = './/a[contains(@href,"/profile/")]/parent::span/following-sibling::span/text()'
                    XPATH_REVIEW_TEXT_1 = './/span[@data-hook="review-body"]//text()'
                    XPATH_REVIEW_TEXT_2 = './/div//span[@data-action="columnbalancing-showfullreview"]/@data-columnbalancing-showfullreview'
                    XPATH_REVIEW_COMMENTS = './/span[@data-hook="review-comment"]//text()'
                    XPATH_AUTHOR  = './/a[contains(@href,"/profile/")]/parent::span//text()'
                    XPATH_REVIEW_TEXT_3  = './/div[contains(@id,"dpReviews")]/div/text()'
                    raw_review_author = review.xpath(XPATH_AUTHOR)
                    raw_review_rating = review.xpath(XPATH_RATING)
                    raw_review_header = review.xpath(XPATH_REVIEW_HEADER)
                    raw_review_posted_date = review.xpath(XPATH_REVIEW_POSTED_DATE)
                    raw_review_text1 = review.xpath(XPATH_REVIEW_TEXT_1)
                    raw_review_text2 = review.xpath(XPATH_REVIEW_TEXT_2)
                    raw_review_text3 = review.xpath(XPATH_REVIEW_TEXT_3)

                    author = ' '.join(' '.join(raw_review_author).split()).strip('By')

                    #cleaning data
                    review_rating = ''.join(raw_review_rating).replace('out of 5 stars','')
                    review_header = ' '.join(' '.join(raw_review_header).split())
                    review_posted_date = dateparser.parse(''.join(raw_review_posted_date)).strftime('%d %b %Y')
                    review_text = ' '.join(' '.join(raw_review_text1).split())

                    #grabbing hidden comments if present
                    if raw_review_text2:
                        json_loaded_review_data = json.loads(raw_review_text2[0])
                        json_loaded_review_data_text = json_loaded_review_data['rest']
                        cleaned_json_loaded_review_data_text = re.sub('<.*?>','',json_loaded_review_data_text)
                        full_review_text = review_text+cleaned_json_loaded_review_data_text
                    else:
                        full_review_text = review_text
                    if not raw_review_text1:
                        full_review_text = ' '.join(' '.join(raw_review_text3).split())

                    raw_review_comments = review.xpath(XPATH_REVIEW_COMMENTS)
                    review_comments = ''.join(raw_review_comments)
                    review_comments = re.sub('[A-Za-z]','',review_comments).strip()
                    review_dict = {
                                    'review_comment_count':review_comments,
                                    'review_text':full_review_text,
                                    'review_posted_date':review_posted_date,
                                    'review_header':review_header,
                                    'review_rating':review_rating,
                                    'review_author':author

                                }
                    reviews_list.append(review_dict)
                if n % 10 == 0:
                    print("Checked " + str(n) + " pages")

            data = {
                        'ratings':ratings_dict,
                        'reviews':reviews_list,
                        'url':amazon_url,
                        'price':product_price,
                        'name':product_name,
                        'asin':asin
                    }
            print("Checked all " + str(n) + " pages")
            return data
        except ValueError:
            print("Retrying to get the correct response")

    return {"error":"failed to process the page","asin":asin}

def ReadAsin(file):
    #Add your own ASINs here
    AsinList = ['B06XQFJM2R','B06XQG4CDX','B06XRX1Z7W','B06XRX2GTQ','B06XSTJST6','B06XZ3J66L','B06Y22HM5S','B06Y2XD9XH','B06ZXXR755','B07121PYWQ','B0713SKWQ1','B0719137DR','B071981FQ6','B071DPZWY9','B071HLPD33','B071KFLT9B','B071KWVVKT','B071L1CXKV','B071LLWLLP','B071NHXCD1','B071P161P5','B071R9N4Z7','B071RPFJ5S','B071VG8KK6','B071VTXDG7','B071VYFJRL','B071W25F4N','B071WM6VBS','B071XX2599','B071Z94F4F','B071ZHHYD9','B071ZYVDMJ','B072142TXK','B07216SSZY','B0721QD57S','B07253MQBM','B0727T67WG','B072B8SZQV','B072BRBK2S','B072BXXWGD','B072F1WBS3','B072HFBFKY','B072J5CLYB','B072KKKTGZ','B072M6Q2D7','B072MPQDYF','B072N4ZR93','B072WQKGDM','B072WSSTD4','B072XWLV4T','B072ZC2KKR','B072ZX8RTZ','B072ZZ3JBF','B0734JD7RF','B0734SZN59','B07361JZ2H','B0736311QF','B073CPTM49','B073GV2PQY','B073JBRNN9','B073JFMP38','B073NQ53ZV','B073QM7L8T','B073RGKSCH','B073WK32VH','B073YSCVVZ','B073Z895LR','B073ZB676Z','B073ZJ3WFT','B074162D49','B07434XJJG','B0743C5GZ5','B074576LSB','B07467GB17','B0746CGV2G','B0746F5Z41','B0746FZJ95','B0746G946P','B0746JTXBM','B0746KB79L','B0749MHYCC','B0749MJG1J','B074BT43B8','B074FZ5563','B074GVPYPY','B074J49F4R','B074J723VJ','B074J8HYBP','B074JDDYY1','B074K3NFZQ','B074LWRLN1','B074MNJ3M3','B074N1Q8GJ','B074N3VCV9','B074N6N9KW','B074NTQ497','B074P1GNZF','B074PKXL57','B074PS5GN2','B074QGK828','B074RBZNPC','B074SFKL9V','B074SGVDK3','B074SYVBBN','B074T9DXX2','B074TDFZHY','B074TFZR9T','B074W95TGS','B074WZ7M84','B074XD5TZT','B074YGV2NK','B074Z53L85','B075175QW4','B07518N24V','B0751FR8JT','B0751WQRTS','B0753Y641T','B07547F8FM','B07553BBY4','B0756B72GV','B0756BJ6MQ','B0756T13FD','B0756V8H57','B0756WX6RK','B0756YZKM7','B07589FB8X','B075CF6QHW','B075CZVHN6','B075D31RYP','B075DJL39W','B075F5BJ3Y','B075FVRSW6','B075G9KL8Q','B075GWQSYH','B075JCFG6S','B075JFWYZ9','B075KPWBBR','B075L27ZB2','B075M689JZ','B075M9ZGDH','B075MB9DFZ','B075MMXBHG','B075MPS4PB','B075N2W1F2','B075Q51S8V','B075Q9P4R1','B075QH6DXK','B075QXSRXK','B075QZZRBJ','B075RWTHQ8','B075RZ4JDC','B075TB89QF','B075VNBHDL','B075WPMB27','B075WWF6XB','B075XBHRZY','B075XGPCJX','B075XK1W3S','B075XL3DRD','B075YQD53N','B075YW2RYT','B075Z14714','B075Z17987','B075ZNZX8J','B075ZQXWFZ','B075ZR1T9K','B075ZZZV8V','B076113SG1','B0761HZ2YG','B0762JQ933','B0763L2JJZ','B0763MB4Q2','B0765VH6C1','B0769G6MTN','B0769R84RF','B076BGHSQS','B076BGJ4VX','B076BRK3Y9','B076BZT4YH','B076CHHBMX','B076F7KG6J','B076H2DZB1','B076HKHSSX','B076HPSYGS','B076J5MYHV','B076J7PR26','B076JCZ313','B076K9PTD5','B076KDVPYB','B076Q5NFB6','B076S8T2MP','B076SBZHMD','B076TVG9LN','B076V18NB6','B076VH2FK3','B076WW5N6F','B076XYBR2D','B076Y5M5SQ','B0771FXWSJ','B0772HL2F7','B0772NZ427','B07746Z365','B07749W5NT','B0774Z4DF9','B0776GCW61','B0779QG7Z7','B077FTQ6RM']
    extracted_data = []

    if os.path.exists(file):
        if input("Are you sure you want to overwrite " + file + "? (y/n)") != "y":
            filename = input("Filename: (without .csv)")
            file = DIR + filename + ".csv"

    with open(file, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Header", "Rating", "Review", "Product", "asin"])
    i = 0

    for asin in AsinList:
        i += 1
        print("Downloading and processing page http://www.amazon.com/dp/"+asin+" - Product "+str(AsinList.index(asin) + 1)+" out of "+str(len(AsinList)))
        data = ParseReviews(asin)
        if "reviews" in data:
            extracted_data.append(data)
        sleep(random.randint(5, 10))
        if i % save_int == 0:
            with open(file, 'a', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                for product in extracted_data:
                    header = []
                    for review in product["reviews"]:
                        writer.writerow([review["review_header"], review["review_rating"], review["review_text"], product["name"], product["asin"]])
            extracted_data = []
            print("Saved " + str(save_int) + " products in " + file)

    with open(file, 'a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        for product in extracted_data:
            header = []
            for review in product["reviews"]:
                writer.writerow([review["review_header"], review["review_rating"], review["review_text"], product["name"],product["asin"]])

if __name__ == '__main__':
    ReadAsin(file)