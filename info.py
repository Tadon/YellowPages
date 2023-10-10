import requests
from bs4 import BeautifulSoup
import csv
import time
filename = 'csv.csv'
counter = 0
for i in range(1, 101):
    

    url = f'https://www.yellowpages.com/search?search_terms=plumbers&geo_location_terms=ca&page={i}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'
    }

    r = requests.get(url, headers=headers)

    mark_soup = BeautifulSoup(r.content, 'html.parser')
    

    mark_html = mark_soup.find_all('div', class_ = 'v-card')

    
    
    for item in mark_html:
        counter += 1
        
        name = item.find('a', class_ = 'business-name').text
        try:
            number = item.find('div', class_= 'phones phone primary').text
        except:
            number = 'No number provided'
        
        try:
            locality = item.find('div', class_='locality').text
        except:
            locality = 'No adress provided'

        try:
            categories = item.find('div', class_= 'categories').text
        except:
            categories = 'No category listed'

        with open(filename, 'a', newline = '') as file:
            write_row = csv.writer(file)
            write_row.writerow([name, locality, number, categories])
        
        

    
    print(counter)