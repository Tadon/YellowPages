import requests
from bs4 import BeautifulSoup
import csv
import time
import os
filename = 'csv.csv'
business_counter = 0
from categories import category_list
from Cities_and_states import Cities_and_states
#adding phone numbers from existing database as keys to ensure no duplicate phone numbers
existing_numbers = {}
headers = ["Company Name", "Company Address", "Company Locality", "Company Phone","Years in business", "Company Website", "Company Email", "Company Categories", "Phone Carrier"]
#verifying existance of header
if not os.path.isfile(filename) or os.stat(filename).st_size == 0:
    with open(filename, 'w', newline = '', encoding = 'utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

with open(filename, 'r',encoding='utf-8') as file:
    reader = csv.reader(file)

    for row in reader:
        existing_numbers[row[3]] = ''
        business_counter += 1
#create dictionary with phone carrier info so we can compare new phone numbers and add carrier to csv file
phone_carrier_dict = {}
with open('phone_carrier.csv', mode='r', newline='', encoding='utf-8') as carrier_file:
    carrier_reader = csv.DictReader(carrier_file)
    for row in carrier_reader:
        phone_carrier_dict[row['Area code + Exchange']] = row['Company']

#begging scraping iteration
for cities in Cities_and_states.California:
    #iterating through categories in the city
    
    for categorie in category_list:
        #iterating through pages of the categories in each city
        counter = 1
        while True:
            
            url = f'https://www.yellowpages.com/search?search_terms={categorie}&geo_location_terms={cities}&page={counter}'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'
            }
            for attempt in range(1000):
                try:
                    r = requests.get(url, headers=headers)
                    break
                except requests.exceptions.ConnectionError:
                    print(f'ConnectionError encountered. Attempt number {attempt + 1}/1000')
                    if attempt < 999:
                        print(f'Sleeping for 5 minutes to retry connection')
                        time.sleep(300.0)
                    else:
                        print(f'Max attempts reached. Unable to complete request.')
                        raise
                except Exception as e:
                    print(f'Unexpected error reached: {e}')
                    raise

            mark_soup = BeautifulSoup(r.content, 'html.parser')
            mark_html = mark_soup.find_all('div', class_ = 'v-card')

            
            #scraping items from each business
            for item in mark_html:
                
                #getting business name
                name = item.find('a', class_ = 'business-name').text
                
                #getting phone number    
                try:
                    number = item.find('div', class_= 'phones phone primary').text
                    number = number.translate({ord(c): None for c in '()- '})
                    number = ''.join(filter(str.isdigit, number))
                except:
                    number = '_No number provided_'
                
                #getting street address
                try:
                    street_address = item.find('div', class_='street-address').text
                except:
                    street_address = '_No address provided_'
                
                #getting business locality
                try:
                    locality = item.find('div', class_='locality').text
                except:
                    locality = '_No locality provided_'
                
                #getting business categories
                try:
                    categories = item.find('div', class_= 'categories').text
                except:
                    categories = '_No category listed_'
                
                #getting more info link for future use of possible email retrieval
                link_element = item.find('a', class_= 'track-more-info')
                if link_element and link_element.has_attr('href'):
                    link = link_element['href']
                else:
                    link = '_More info not found_'
                email = '_No Email Provided_'

                #getting company website                
                try:
                    website = mark_soup.find('a', class_='track-visit-website')
                    company_website = website['href']
                except:
                    company_website = '_No Website Provided_'

                #Getting years in business
                badges = mark_soup.find('div', class_ = 'badges')
                if badges:
                    years_in_business_check = badges.find('div', class_ = 'years-in-business')
                    if years_in_business_check:
                        years = years_in_business_check.find('strong').get_text(strip=True)
                    else:
                        years = '_Years Not Given_'
                else:
                    years = '_Years Not Given_'
                

                if (number not in existing_numbers) and number != '_No number provided_':
                    

                    if link != '_More info not found_':
                        new_url = f'https://www.yellowpages.com{link}'
                        nr = requests.get(new_url, headers=headers)
                        new_soup = BeautifulSoup(nr.content, 'html.parser')
                        email_link = new_soup.find('a', class_='email-business')

                        if email_link:
                            try:
                                email = email_link['href'].split('mailto:')[-1]
                            except:
                                pass
                        else:
                            pass
                            
                    else:
                        pass
                    
                        
                    area_exchange_code = number.translate({ord(c): None for c in '()- '})
                    area_exchange_code = area_exchange_code[:6]
                    phone_carrier = phone_carrier_dict.get(area_exchange_code, '_No Carrier Found_')

                    with open(filename, 'a', newline = '', encoding = 'utf-8') as file:
                        write_row = csv.writer(file)
                        write_row.writerow([name, street_address, locality, number,years,company_website, email, categories, phone_carrier])
                    business_counter += 1

                existing_numbers[number] = ''

            print(f'Processed page {counter} of {categorie} in {cities}, with a total of {business_counter} businesses added.')

            next_page_exists = mark_soup.find('a', class_= 'next ajax-page')
            if next_page_exists:
                counter += 1
            else:
                break

print('Scraping complete!')