import json

import time

import sys
from selenium import webdriver
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains


def get_elements_detail(element):
    data = {}
    try:
        title_element = element.find_elements_by_class_name("title-line")
        title = title_element[0].text
        data['title'] = title
    except Exception as E:
        print(E, 'title')

    try:
        loc_link_element = element.find_elements_by_class_name('locWrap')
        location = loc_link_element[0].text
        data['location'] = location
    except Exception as E:
        print(E, 'location')

    try:
        href = loc_link_element[0].find_elements_by_class_name('loclink')[0].get_attribute('href')
        data['href'] = href
    except Exception as E:
        print(E, 'href')

    try:
        image_figure = element.find_elements_by_tag_name('figure')[0]
        actions = ActionChains(browser)
        actions.move_to_element(image_figure).perform()
        while True:

            try:
                image_chevron = element.find_elements_by_class_name('icon-chevron-right')[0]
                if 'disable' not in element.find_elements_by_class_name('btn-next')[0].get_attribute('class'):
                    image_chevron.click()
                    time.sleep(1)
                    continue
                else:
                    break

            except Exception as E:
                print(E, 'next image chevron error')
                break

        image_links = [j.get_attribute('data-src') for j in element.find_elements_by_tag_name('img')]
        data['image_links'] = image_links
    except Exception as E:
        print(E, 'image_links', sys.exc_info()[2].tb_lineno)

    try:
        city_name = element.find_elements_by_class_name('cityName')[0].text
        data['city_name'] = city_name
    except Exception as E:
        print(E, 'city_name')

    try:
        description = element.find_elements_by_class_name('listing-description')[0].text
        data['description'] = description
    except Exception as E:
        print(E, 'description')

    try:
        listing_highlights_table = element.find_elements_by_class_name('listing-highlights')[0].get_attribute(
            "outerHTML")
        listing_highlights_table_dataframe = pd.read_html(listing_highlights_table)[0].dropna()
        json_highlight_data = json.loads(listing_highlights_table_dataframe.set_index('Specifications.1').to_json())
        for current_key in json_highlight_data['Specifications']:
            data[current_key] = json_highlight_data['Specifications'][current_key]
    except Exception as E:
        print(E, 'listing_highlights')

    return data


result = []
ctr = 0

browser = webdriver.Chrome('/home/nimish/PycharmProjects/MyProjects/so/internship/macroproject/chromedriver')
start_page = 1

page_no = start_page
stop_page = 2

while page_no <= stop_page:
    url = 'https://www.makaan.com/delhi-residential-property/rent-property-in-delhi-city?page=' + str(page_no)

    browser.get(url)
    time.sleep(5)

    elements_list = browser.find_elements_by_css_selector('div[data-type="listing-card"]')
    for element in elements_list:
        print(ctr)
        result.append(get_elements_detail(element))
        ctr += 1

    page_no += 1

pd.DataFrame(result).to_excel(
    "/home/nimish/Desktop/makaan_files/resultsfrom" + str(start_page) + "to" + str(stop_page) + ".xlsx")
