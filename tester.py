import psycopg2
import requests
from bs4 import BeautifulSoup
import time
from categories import category_list
from Cities_and_states import Cities_and_states
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

#importing cities and states class to provide easy iteration
cities_and_states_full = Cities_and_states.city_and_states_full
cities_and_states_abridged = Cities_and_states.cities_and_states_abridged
counter = 0
iterating_location_dict = {}
for i in range(200):
    for city_num, cities in cities_and_states_full.items():
        if i < len(cities):
            key = f'City # {i+1}'
            if key not in iterating_location_dict:
                iterating_location_dict[key] = []
                
            iterating_location_dict[key].append(cities[i])
            
for cities in iterating_location_dict['City # 1']:
    counter += 1
    print(cities)

