import psycopg2
import requests
from bs4 import BeautifulSoup
import time
from categories import category_list
from Cities_and_states_new import Cities_and_states
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
current_time = time.localtime()
start_time = time.strftime('%H:%M:%S', current_time)
starttime = time.time()
#importing cities and states class to provide easy iteration via dictionary
cities_and_states_full = Cities_and_states.city_and_states_full
cities_and_states_abridged = Cities_and_states.cities_and_states_abridged
#creating dictionary that iterated through first city of each state, then second city of each state, etc...
iterating_dictionary = {}
for i in range(200):
    for state, cities in cities_and_states_full.items():
        if i < len(cities):
            key = f'City #{i+1}'
            if key not in iterating_dictionary:
                iterating_dictionary[key] = []
            iterating_dictionary[key].append(cities[i])
#creating requests function to handle http errors    
def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


session = requests_retry_session()

# Database connection parameters
db_params = {
    'dbname': 'YP_1',
    'user': 'postgres',
    'password': 'Lolwat123!@#',
    'host': 'localhost'
}
try:
    # Connect to the database
    conn = psycopg2.connect(**db_params)

    # Adding phone numbers from existing database as keys to ensure no duplicate phone numbers
    cur = conn.cursor()
    cur.execute('SELECT "Company Phone" FROM yp_dump')
    rows = cur.fetchall()
    business_counter = 0
    existing_numbers = {}
    for row in rows:
        phone_number = row[0]
        existing_numbers[phone_number] = ''
        business_counter += 1    
    
    # Create a dictionary with phone carrier info
    cur = conn.cursor()
    cur.execute('SELECT acex,"Company" FROM carrier_db')
    rows = cur.fetchall()
    phone_carrier_dict = {row[0]: row[1] for row in rows}

    session_counter = 0
    # Iterating through states of dictionary
    for city_number,cities in iterating_dictionary.items():
        #Iterating through cities in states
        for city in cities:
        # Iterating through categories in the city
            for categorie in category_list:
                # Iterating through pages of the categories in each city
                counter = 1
                while True:
                    url = f'https://www.yellowpages.com/search?search_terms={categorie}&geo_location_terms={city}&page={counter}'
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'
                    }
                    success = False
                    for attempt in range(1000):
                        try:
                            r = session.get(url, headers=headers, timeout=10)
                            success = True
                            break
                        except requests.exceptions.RequestException as e:
                            print(f'Request failed: {e}, attempt {attempt + 1}/1000')
                            if attempt >= 999:
                                print("Max attempts reached, moving to next.")
                                break
                            time.sleep(5)  # Wait 5 seconds before retrying

                    if not success:
                        continue

                    mark_soup = BeautifulSoup(r.content, 'html.parser')
                    mark_html = mark_soup.find_all('div', class_='v-card')

                    # Scrape items from each business
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
                            website = item.find('a', class_='track-visit-website')
                            company_website = website['href']
                        except:
                            company_website = '_No Website Provided_'

                        #Getting years in business
                        badges = item.find('div', class_ = 'badges')
                        if badges:
                            years_in_business_check = badges.find('div', class_ = 'years-in-business')
                            if years_in_business_check:
                                years_in_business = years_in_business_check.find('strong').get_text(strip=True)
                            else:
                                years_in_business = '_Years Not Given_'
                        else:
                            years_in_business = '_Years Not Given_'
                        

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

                        
                            # Define the INSERT query
                            query = '''
                            INSERT INTO yp_dump ("Company Name", "Company Address", "Company Locality", "Company Phone", "Years in Business", "Company Website", "Company Email", "Company Categories", "Phone Carrier")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            '''
                            # Data to insert
                            data = (name, street_address, locality, number, years_in_business, company_website, email, categories, phone_carrier)

                            # Execute the insert statement
                            with conn.cursor() as cur:
                                cur.execute(query, data)
                                conn.commit()
                            session_counter += 1
                            business_counter += 1
                            existing_numbers[number] = ''
                    currenttime = time.time()
                    elapsedtime = (currenttime - starttime)
                    elapsedtime_inhrs = elapsedtime / 3600
                    addition_per_hr = session_counter / elapsedtime_inhrs
                    
                    formatted_elapsedtime = '{:.2f}'.format(elapsedtime_inhrs)
                    print(f'Processed page: {counter} of {categorie} in {city} - Daily count:{session_counter} - Total count: {business_counter} - Start time: {start_time}AM - Time Elapsed: {formatted_elapsedtime}Hours - Additions/hr = {addition_per_hr:.2f} ')

                    next_page_exists = mark_soup.find('a', class_='next ajax-page')
                    if next_page_exists:
                        counter += 1
                    else:
                        break

    # Close the database connection
    conn.close()

    print('Scraping complete!')
finally:
    cur.close()
    conn.close()
    