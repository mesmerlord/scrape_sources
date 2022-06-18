from lncrawl.core.sources import *
import json
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from operator import itemgetter
import random
import logging
import urllib3
from colorama import Fore
import concurrent.futures
import traceback
import requests
import ssl
import tldextract

urllib3.disable_warnings()

logging.basicConfig(
            level=logging.DEBUG,
            format=Fore.CYAN + '%(asctime)s '
            + Fore.RED + '[%(levelname)s] '
            + Fore.YELLOW + '(%(name)s)\n'
            + Fore.WHITE + '%(message)s' + Fore.RESET,
        )
logger = logging.getLogger(__name__)

load_sources()
allCrawlers = crawler_list
blocked_sources = ["anythingnovel","automtl" , 'qidian', "writerupdates", "dsrealm", "divinedaolib",
    "novelspread", "oppa", "babel", "instadoses", "rebirthonline", "fourscan", "novelmao", 
    "readlightnovel", "gravitytales", "novelraw", "lightnovelworld"]

# novel_names = pd.read_csv("newfile3.csv")['Book Name'].values.tolist()
def get_novel_names():
    with open("novel_data.json") as f:
        novel_data = json.load(f)
    novels = []
    for page in novel_data:
        for novel in novel_data[page]:
            novels.append(novel['name'])

    return novels

def get_good_sources():
    df = pd.read_csv("sources.csv")['source'].values.tolist()
    good_sources = []
    sources_to_use = []
    
    for source in df:
        source_domain = tldextract.extract(source)
        good_sources.append(source_domain.domain)

    for x in allCrawlers:
        crawler_domain = tldextract.extract(str(x))
        if crawler_domain.domain in good_sources:
            sources_to_use.append(x)
            try:
                crawl = allCrawlers[x]
                sources_to_use.append(crawl)
            except TypeError:
                pass
    return sources_to_use

novel_names = get_novel_names()
crawlers = get_good_sources()
errors = {}
not_found = []


def get_chapters_len(crawler_instance):
    crawler_instance.read_novel_info()
    if len(crawler_instance.chapters) == 0:
        return
    elif len(crawler_instance.chapters) > 0:
        return [len(crawler_instance.chapters), crawler_instance.novel_url]
        
def get_info(crawler, query):
    newCrawl = crawler()
    novel_info = {}
    results = []
    url = newCrawl.base_url
    novel_info = newCrawl.search_novel(query=query)
    for novel in novel_info:
        if novel['title'] == query:
            newCrawl.novel_url = novel['url']
            logger.info(f"Found novel at : {novel['url']}")
            results =  get_chapters_len(newCrawl)

    newCrawl.destroy()
    if results:
        logger.info(f"{query} Novel found")
        return results
    else:
        return None

def single_search(query, crawler_instances):
    final_list = []
    num_of_crawlers = len(crawler_instances)
    with ThreadPoolExecutor(max_workers=num_of_crawlers) as executor:
        future_to_url = {executor.submit(get_info, crawler_instance, query):
                 crawler_instance for crawler_instance in crawler_instances}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result(timeout = 3)
                if result:
                    final_list.append(result)
            except (TypeError, requests.exceptions.SSLError,ssl.SSLEOFError, 
                urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError, requests.exceptions.MissingSchema,
                AttributeError,requests.exceptions.ReadTimeout ):
                print("wrong")
                pass
            
            except Exception as exc:
                print(traceback.format_exc())
                # print('%r generated an exception: %s' % (url, exc))

    return final_list
novels_list = {}

with open('data.json', 'r', encoding='utf-8') as json_file:
    novels_list = json.load(json_file)
with open('not_found.json', 'r', encoding='utf-8') as json_file_2:  
    not_found = json.load(json_file_2)

novel_names = [x for x in novel_names if x not in novels_list.keys()][:20]
for num, novel in enumerate(novel_names):
    list_of_results = []
    final = []
    items_to_search = 50
    random.shuffle(crawlers)

    for x in range(0, len(crawlers), items_to_search):
        crawler_list_slice = crawlers[x : x + items_to_search]
        semi_final = single_search(novel, crawler_list_slice)
        if semi_final:
            final = final + semi_final
        logger.info(f"{len(final)} -- {novel}")
        if len(final) >= 5:
            break
    if final:
        data = sorted(final, key=itemgetter(0), reverse=True)
        novels_list[novel] = data
        logger.info(f"{num} --  Finished novel : {novel} ")
    else:
        logger.error(f"{num} --  Not found : {novel} ")
        novels_list[novel] = final
        not_found.append(novel)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(novels_list, f, ensure_ascii=False, indent=2)
    with open('not_found.json', 'w', encoding='utf-8') as not_f:
        json.dump(not_found, not_f, ensure_ascii=False, indent=2)

