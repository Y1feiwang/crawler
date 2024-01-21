import logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import os
import threading
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import scrolledtext  # Import scrolledtext for a scrollable text area
import re
import sys
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

class Crawler:
    kwds={}
    kwd_counter=0
    kwd_stat=pd.DataFrame(columns=['time', 'num_keyword'])
    doc_stat=pd.DataFrame(columns=['time', 'num_URL'])
    ratio_stat=pd.DataFrame(columns=['time', 'num_crawled_ovr_be_crawled'])
    cur_url=""

    doc_counter=0
    end=False
    def __init__(self, urls=[], callback=None):
        self.visited_urls = []
        self.urls_to_visit = urls
        self.callback = callback
        self.running=False

    def record_data(self):
        tm = 0
        while self.running:
            time.sleep(60)
            tm+=1
            print(self.kwd_counter)
            print(self.doc_counter)
            print(self.doc_counter/len(self.urls_to_visit))
            self.kwd_stat.loc[len(self.kwd_stat)] = [tm, self.kwd_counter]
            self.doc_stat.loc[len(self.doc_stat)] = [tm, self.doc_counter]
            self.ratio_stat.loc[len(self.ratio_stat)] = [tm, self.doc_counter/len(self.urls_to_visit)]

    def download_url(self, url):
        response = requests.get(url)
        # download webpage
        if not os.path.exists('webpages'):
            os.mkdir('webpages')
        f = open(f"webpages/{self.doc_counter}.txt", "w")
        f.write(response.text)

        # record keywords
        soup = BeautifulSoup(response.text, 'html.parser')
        lst=soup.get_text().split()
        for i in lst:
            if i in self.kwds:
                if self.doc_counter not in self.kwds[i]:
                    self.kwds[i].append(self.doc_counter)
            else:
                self.kwds[i]=[self.doc_counter]
            self.kwd_counter+=1
        return response.text

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)
            yield path

    def add_url_to_visit(self, url):
        if url not in self.visited_urls and url not in self.urls_to_visit:
            self.urls_to_visit.append(url)
 
    def crawl(self, url):
        html = self.download_url(url)
        for url in self.get_linked_urls(url, html):
            self.add_url_to_visit(url)

    def write_kwd_and_stats(self):
        pattern = re.compile(r'^stats-(\d+)$')

        max_number = -1
        for entry in os.listdir('.'):
            if os.path.isdir(entry):
                match = pattern.match(entry)
                if match:
                    number = int(match.group(1))
                    if number > max_number:
                        max_number = number

       
        if max_number==-1:
            new_folder="stats-0"
        else:
             new_folder = f"stats-{max_number + 1}"
        
        os.makedirs(new_folder)

        with open(new_folder+'/keywords.txt', 'w') as keywords_file: 
            keywords_file.write(json.dumps(self.kwds))
        self.doc_stat.to_csv(new_folder+'/doc_stat.csv')
        self.kwd_stat.to_csv(new_folder+'/kwd_stat.csv')
        self.ratio_stat.to_csv(new_folder+'/ratio_stat.csv')

        # Plotting for kwd_stat
        plt.figure()
        plt.plot(self.kwd_stat['time'], self.kwd_stat['num_keyword'])
        plt.xlabel('Time')
        plt.ylabel('Number of Keywords')
        plt.title('Keywords Over Time')
        plt.savefig(new_folder+'/kwd_stat_plot.png')

        # Plotting for doc_stat
        plt.figure()
        plt.plot(self.doc_stat['time'], self.doc_stat['num_URL'])
        plt.xlabel('Time')
        plt.ylabel('Number of URLs')
        plt.title('URLs Over Time')
        plt.savefig(new_folder+'/doc_stat_plot.png')

        # Plotting for ratio_stat
        plt.figure()
        plt.plot(self.ratio_stat['time'], self.ratio_stat['num_crawled_ovr_be_crawled'])
        plt.xlabel('Time')
        plt.ylabel('Crawled/To Be Crawled Ratio')
        plt.title('Crawled/To Be Crawled Ratio Over Time')
        plt.savefig(new_folder+'/ratio_stat_plot.png')

    def run(self,max_pages=1000):
        self.record=threading.Thread(target=self.record_data)
        self.record.start()
        self.running=True
        while self.urls_to_visit and (self.doc_counter <= max_pages) and self.running:
            url = self.urls_to_visit.pop(0)
            logging.info(f'Crawling: {url}')
            # if self.callback:
            #     self.callback(f"Crawling: {url}")
            self.cur_url=url
            try:
                self.crawl(url)
                self.doc_counter +=1
            except Exception:
                logging.exception(f'Failed to crawl: {url}')
                continue
            finally:
                self.visited_urls.append(url)
        self.stop()

    def stop(self):
        self.running=False
        self.record.join()
        self.write_kwd_and_stats()
        
import tkinter as tk
from tkinter import scrolledtext

class CrawlerGUI:
    
    def __init__(self, master):
        self.crawler=None
        self.crawl_thread=None
        self.master = master
        status=threading.Thread(target=self.check_crawler_ending)
        status.daemon=True
        status.start()
        master.title("Web Crawler")

        # URL Input
        self.label_url = tk.Label(master, text="Enter Seed URL")
        self.label_url.pack()
        self.entry_url = tk.Entry(master, width=50)
        self.entry_url.pack()

        # Max Pages Input
        self.label_max_pages = tk.Label(master, text="Enter Maximum Number of Pages")
        self.label_max_pages.pack()
        self.entry_max_pages = tk.Entry(master)
        self.entry_max_pages.pack()

        # Start Button
        self.start_button = tk.Button(master, text="Start Crawling", command=self.start_crawling)
        self.start_button.pack()

        # Status Text Area
        self.status_area = scrolledtext.ScrolledText(master, wrap=tk.WORD)
        self.status_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Stop Button (if applicable)
        self.stop_button = tk.Button(master, text="Stop Crawling", command=self.stop_crawling)
        self.stop_button.pack()

        master.protocol("WM_DELETE_WINDOW", self.stop_crawling)
    def check_crawler_ending(self):
        while self.crawler is None:
            time.sleep(2)
        while self.crawler.running:
            time.sleep(2)
        self.stop_crawling()
    def start_crawling(self):

        url = self.entry_url.get()
        max_pages = self.entry_max_pages.get()
        if url and max_pages:
            self.crawler=Crawler(urls=[url])
            self.crawl_thread = threading.Thread(target=self.crawler.run, args=[int(max_pages)])
            self.crawl_thread.start()
            
            self.status_area.insert(tk.END, f"Starting crawl at {url} with max pages {max_pages}\n")
            # self.update_text_area()


    def stop_crawling(self):
        if self.crawler:
            if self.crawler.running:
                self.crawler.stop()
            if self.crawl_thread.is_alive() is False:
                self.crawl_thread.join()
            self.status_area.insert(tk.END, "Crawl stopped\n")
            self.crawler = None
            self.crawl_thread = None
        self.master.destroy()  # Destroy the Tkinter window

if __name__ == '__main__':
    Crawler(urls=['https://cc.gatech.edu']).run(max_pages=2000)
    # https://cc.gatech.edu
    # root = tk.Tk()
    # gui = CrawlerGUI(root)
    # root.mainloop()
