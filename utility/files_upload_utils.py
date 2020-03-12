import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import time

browser = webdriver.Chrome(
    executable_path='/home/nimish/PycharmProjects/MyProjects/so/internship/macroproject/chromedriver')
browser.get('https://api.halanx.com/admin/halanxhomes/Houses/amenity/add/')

username = 'nimish'
password = ''
if not password:
    raise Exception('set password')

browser.find_element_by_name('username').send_keys(username)
browser.find_element_by_name('password').send_keys(password)
browser.find_element_by_id('login-form').submit()

path_to_files = '/home/nimish/important_projects/ConsumerAppBackend/files/amenties_image/websiteassetssvg/'
for file in os.listdir(path_to_files)[:1]:
    file_name = file.split(".")[0]
    browser.find_element_by_name('name').send_keys(file_name)
    select_category = Select(browser.find_element_by_name('category'))
    select_category.select_by_value('inhouse')
    image_field_id = 'id_svg'
    image_path = os.path.join(path_to_files, file)
    browser.find_element_by_id(image_field_id).send_keys(image_path)

