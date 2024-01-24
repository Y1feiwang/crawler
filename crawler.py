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
    def __init__(self, urls=[], callback=None,domain=""):
        self.visited_urls = []
        self.urls_to_visit = urls
        self.callback = callback
        self.running=False
        self.domain=domain

    def record_data(self):
        print("start recording data")
        tm = 0
        while self.running:
            # time.sleep(60)
            
            for i in range(30):
                time.sleep(2)
                if self.running is False:
                    break
                    
            tm+=1
            print(self.kwd_counter)
            print(self.doc_counter)
            print(self.doc_counter/len(self.urls_to_visit))
            self.kwd_stat.loc[len(self.kwd_stat)] = [tm, self.kwd_counter]
            self.doc_stat.loc[len(self.doc_stat)] = [tm, self.doc_counter]
            self.ratio_stat.loc[len(self.ratio_stat)] = [tm, self.doc_counter/len(self.urls_to_visit)]
        print("stop recording data")

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
                    self.kwds[i][self.doc_counter]=1
                else:
                    self.kwds[i][self.doc_counter]+=1
            else:
                self.kwds[i]={self.doc_counter:1}
            self.kwd_counter+=1
        return response.text

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)
            if path is not None:
                yield path

    def add_url_to_visit(self, url):
            # Check if the URL belongs to the 'https://cc.gatech.edu' domain
        if self.domain in url:
            if url not in self.visited_urls and url not in self.urls_to_visit:
                self.urls_to_visit.append(url)
        # if url not in self.visited_urls and url not in self.urls_to_visit:
        #     self.urls_to_visit.append(url)
 
    def crawl(self, url):
        html = self.download_url(url)
        for url in self.get_linked_urls(url, html):
            self.add_url_to_visit(url)

    def write_kwd_and_stats(self):
        print("writing data to file")
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
        print("finished writing data to file")

    def run(self,max_pages=10000000):
        self.record=threading.Thread(target=self.record_data)
        self.running=True
        self.record.start()
        
        while self.urls_to_visit and (self.doc_counter <= max_pages) and self.running:
            url = self.urls_to_visit.pop(0)
            logging.info(f'Crawling: {url}')
            self.cur_url=url
            try:
                self.crawl(url)
                self.doc_counter +=1
            except Exception:
                logging.exception(f'Failed to crawl: {url}')
                continue
            finally:
                self.visited_urls.append(url)
        self.record.join()
        self.write_kwd_and_stats()
        print("finished running crawler run ")
    def stop(self):
        print("crawler's internal stop called")
        self.running=False

        
import tkinter as tk
from tkinter import scrolledtext

class CrawlerGUI:
    
    def __init__(self, master):
        self.crawler=None
        self.crawl_thread=None
        self.master = master

        master.title("Web Crawler")

        # URL Input
        self.label_url = tk.Label(master, text="Enter Seed URL")
        self.label_url.pack()
        self.entry_url = tk.Entry(master, width=50)
        self.entry_url.pack()

        # Max Pages Input
        self.domain = tk.Label(master, text="Enter the domain you want to crawl on")
        self.domain.pack()
        self.entry_domain = tk.Entry(master, width=50)
        self.entry_domain.pack()

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
        
    def start_crawling(self):

        url = self.entry_url.get()
        max_pages = self.entry_max_pages.get()
        domain = self.entry_domain.get()
        if url:
            if domain:
                self.crawler=Crawler(urls=[url],domain=domain)
                print("DOMAIN ",domain)
            else:
                self.crawler=Crawler(urls=[url])  
            
            if max_pages:
                print("max pages",max_pages)
                self.crawl_thread = threading.Thread(target=self.crawler.run, args=[int(max_pages)])
                self.status_area.insert(tk.END, f"Starting crawl at {url} with max pages {max_pages}\n")
            else:
                self.crawl_thread = threading.Thread(target=self.crawler.run)
                self.status_area.insert(tk.END, f"Starting crawl at {url} with no max pages")
                
            self.update_status=threading.Thread(target=self.update_text_area, args=[max_pages])
            
            self.crawl_thread.start() 
            self.update_status.start()  
            
            # self.update_text_area()

    def update_text_area(self,max_pages):
        self.seconds = time.time()
        while self.crawler.running:
            time.sleep(3)
            if self.crawler.running:
                print("SHOUDL BE PRINTING NOW")
                self.status_area.insert(tk.END, f"Crawled {self.crawler.doc_counter} pages; ")
                self.status_area.insert(tk.END, f"found {self.crawler.kwd_counter} keywords.\n")
                if max_pages:
                    self.status_area.insert(tk.END, f"progress: {self.crawler.doc_counter/int(max_pages)}%\n")
        
    def stop_crawling(self):
        print("SHOULD BE STOPPing")
        # if self.crawler:
        self.status_area.insert(tk.END, f"---------Summary----------\n")
        self.status_area.insert(tk.END, f"Timer for this crawling: {time.time()-self.seconds}\n")
        self.status_area.insert(tk.END, f"Crawled {self.crawler.doc_counter} pages\n")
        self.status_area.insert(tk.END, f"found {self.crawler.kwd_counter} keywords.\n")   
        if self.crawler.running:
            print("crawler stopped")
            self.crawler.stop()
            print(self.crawler.running)
        if self.crawl_thread.is_alive():
            print('crawler thread joined')
            self.crawl_thread.join()
            print('joined?')
        if self.update_status.is_alive():
            print('update status thread joined')
            self.update_status.join()
        else:
            print('update status not alivve?')
        print('crawl stopped')
        self.status_area.insert(tk.END, "Crawl stopped\n")
        self.crawler = None
        self.crawl_thread = None

if __name__ == '__main__':
    Crawler(urls=['https://cc.gatech.edu'],domain='cc.gatech.edu').run(max_pages=3000)
    # root = tk.Tk()
    # gui =CrawlerGUI(root)
    # root.mainloop()