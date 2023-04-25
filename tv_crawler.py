from io import TextIOWrapper
import re
from bs4 import BeautifulSoup
from urllib import parse
import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG, filename='output.log', filemode='w')
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
visitlog = logging.getLogger('visited')

class Site:
    def __init__(self:str, link:str, key_path:str, page:str, info:str):
        self.link = link
        self.key_path = key_path
        self.page = int(page)
        self.info = info

    def __str__(self):
        return 'Link: '+self.link+'\nKey path: '+self.key_path+'\nPage: '+self.page+'\nInfo: '+self.info+'\n'

# retrieves all links in a given link
def get_links(url:str, key_path:str)->list[str]:
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return [parse.urljoin(url, link.get('href')) for link in soup.find_all('a', href=re.compile('.*'+key_path+'.*'))]

title = 'Title'
description = 'Description'
genre = 'Genre'
actor = 'Actor'
director = 'Director'
country = 'Country'
duration = 'Episode Duration'
quality = 'Quality'
release = 'Release'
rating = 'Rating'
link = 'Link'

# get specific site's content
def read_bmovies(url:str):
    data = {}
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    div = soup.find('div', {'class':'mvic-desc'})
    details = [item.get_text(strip=True).split(':') for item in div.find('div', {'class':'mvic-info'}).find_all('p')]
    # title
    data[title] = div.find('h3').get_text(strip=True)
    data[description] = div.find('div', {'class':'desc'}).get_text(strip=True)
    data[genre] = details[0][1]
    data[actor] = details[1][1]
    data[director] = details[2][1]
    data[country] = details[3][1]
    data[duration] = details[5][1]
    data[quality] = details[6][1]
    data[release] = details[7][1]
    data[rating] = details[8][1]
    data[link] = url
    return data

# get specific site's content
def read_dopebox(url:str):
    data = {}
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    div = soup.find('div', {'class':'dp-i-c-right'})
    details = [item.get_text(strip=True).split(':') for item in div.find_all('div', {'class':'row-line'})]
    data[title] = div.find('h2', {'class':'heading-name'}).get_text(strip=True)
    data[description] = div.find('div', {'class':'description'}).get_text(strip=True).split('Overview:')[1]
    data[genre] = details[1][1]
    data[actor] = details[2][1]
    data[director] = details[5][1]
    data[country] = details[4][1]
    data[duration] = div.find('span', {'class':'duration'}).get_text(strip=True)
    data[quality] = div.find('span', {'class':'quality'}).get_text(strip=True)
    data[release] = details[0][1]
    data[rating] = div.find('span', {'class':'imdb'}).get_text(strip=True).split('IMDB: ')[1]
    data[link] = url
    return data

def read_moviecrumbs(url:str):
    data = {}
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    div = soup.find('div', {'class':'dp-i-c-right'})
    details = [item.get_text(strip=True).split(':') for item in div.find_all('div', {'class':'row-line'})]
    data[title] = div.find('h2', {'class':'heading-name'}).get_text(strip=True)
    data[description] = div.find('div', {'class':'description'}).get_text(strip=True)
    data[genre] = details[1][1]
    data[actor] = details[2][1]
    data[director] = details[5][1]
    data[country] = details[4][1]
    data[duration] = details[3][1].replace('\n', '')
    data[quality] = div.find('button', {'class':'btn btn-sm btn-quality'}).get_text(strip=True)
    data[release] = details[0][1]
    data[rating] = div.find('span', {'class':'item mr-2'}).get_text(strip=True).split('IMDB: ')[1]
    data[link] = url
    return data

def crawl_n_scrape(site:Site, get_content:int):
    res={}
    data = []
    visited = []
    for i in range(site.page):
        links = get_links(site.link+str(i+1), site.key_path)
        for link in links:
            if link in visited:
                continue
            visitlog.debug(link)
            data.append(get_content(link))
            visited.append(link)
    res[site.link] = data
    return res

def writelines(filename, data):
    with open(filename, 'w') as fout:
        for d in data:
            print(d, file=fout)

# read file into list[Site]
def get_sites(filename)->list[Site]:
    with open(filename, 'r') as f:
        lines = f.read().splitlines()

    sites = []
    site = None
    for line in lines:
        if line.startswith('Link: '):
            link = line.split('Link: ')[1]
            site = Site(link, '', '0', '')
        elif line.startswith('Key path: '):
            site.key_path = line.split('Key path: ')[1]
        elif line.startswith('Page: '):
            site.page = line.split('Page: ')[1]
        elif line.startswith('Info: '):
            site.info = line.split('Info: ')[1]
            sites.append(site)
            # print(site)

    return sites


if __name__ == '__main__':
    sites = get_sites("roots.txt")

    data_json = open('data.json', 'w')
    data = []
    get_functions=[read_bmovies, read_dopebox, read_moviecrumbs]
    iterator = 0
    for site in sites:
        data.append(crawl_n_scrape(site, get_functions[iterator]))
        iterator+=1
    print(json.dump(data, data_json))
    data_json.close()

