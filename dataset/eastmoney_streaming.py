import requests
import os
from lxml import etree
from tqdm import tqdm
import pandas as pd
import json
import pdb
from _base import Downloader


class Eastmoney_Streaming(Downloader):

    def __init__(self, args={}):
        super().__init__(args)
        self.dataframe = pd.DataFrame()

    # def download_streaming_stock(self, stock = "600519", rounds = 3):
    #     print( "Geting pages: ", end = "")
    #     if rounds > 0:
    #         for r in range(rounds):
    #             br = self._gather_pages(stock, r)
    #             if br == "break":
    #                 break
    #     else:
    #         r = 1
    #         error_count = 0
    #         while 1:
    #             br = self._gather_pages(stock, r)
    #             if br == "break":
    #                 break
    #             elif br == "Error":
    #                 error_count +=1
    #             if error_count>10:
    #                 print("Connection Error")
    #             r += 1
    #     print( f"Get total {r+1} pages.")
    #     self.dataframe = self.dataframe.reset_index(drop = True)
    
    # def _gather_pages(self, stock, page):
    #     print( page, end = " ")
    #     url = f"https://guba.eastmoney.com/list,{stock},1,f_{page}.html"
    #     headers = {
    #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    #     }

    #     requests.DEFAULT_RETRIES = 5  # 增加重试连接次数
    #     s = requests.session()
    #     s.keep_alive = False  # 关闭多余连接
        
    #     response = self._request_get(url, headers=headers)
    #     if response.status_code != 200:
    #         return "Error"
        
    #     # gather the comtent of the first page
    #     # pdb.set_trace()
    #     page = etree.HTML(response.text)
    #     trs = page.xpath('//*[@id="mainlist"]/div/ul/li[1]/table/tbody/tr')
    #     have_one = False
    #     for item in trs:
    #         have_one = True
    #         read_amount = item.xpath("./td[1]//text()")[0]
    #         comments = item.xpath("./td[2]//text()")[0]
    #         title = item.xpath("./td[3]/div/a//text()")[0]
    #         content_link = item.xpath("./td[3]/div/a/@href")[0]
    #         author = item.xpath("./td[4]//text()")[0]
    #         time = item.xpath("./td[5]//text()")[0]
    #         tmp = pd.DataFrame([read_amount, comments, title, content_link, author, time]).T
    #         columns = [ "read amount", "comments", "title", "content link", "author", "create time" ]
    #         tmp.columns = columns
    #         self.dataframe = pd.concat([self.dataframe, tmp])
    #         #print(title)
    #     if have_one == False:
    #         return "break"
    
    # gte the single reporter list all for subsequent download
    def download_single_reporter_list_all(self):
        list_url = "https://reportapi.eastmoney.com/report/list2"
        list_post_data_pageNo_max = 1755
        eastmoney_single_reporter_list_all_path = './data/eastmoney_single_reporter_list_all.json'
        if os.path.exists(eastmoney_single_reporter_list_all_path):
            os.remove(eastmoney_single_reporter_list_all_path)
        for pageNo in tqdm(range(1, list_post_data_pageNo_max + 1)):
            list_post_data = '{"beginTime":"2000-09-25","endTime":"2024-11-24","industryCode":"*","ratingChange":null,"rating":null,"orgCode":null,"code":"*","rcode":"","pageSize":100,"pageNo":' + str(pageNo) + '}'
            list_post_data = json.loads(list_post_data)
            response = self._request_post(url=list_url, json=list_post_data)
            try:
                data = json.loads(response.text)['data']
            except Exception as e:
                print(e, pageNo)
            try:
                with open(eastmoney_single_reporter_list_all_path, 'a', encoding='utf8') as f:
                    for data_item in data:
                        f.write(json.dumps(data_item, ensure_ascii=False) + '\n')
            except Exception as e:
                print(e, pageNo)
    
    def download_industry_reporter_list_all(self):
        list_url = "https://reportapi.eastmoney.com/report/list?pageSize=100&beginTime=2000-09-26&endTime=2024-11-24&pageNo=4&qType=1"
        list_get_data_pageNo_max = 1760
        eastmoney_single_reporter_list_all_path = './data/eastmoney_industry_reporter_list_all.json'
        if os.path.exists(eastmoney_single_reporter_list_all_path):
            os.remove(eastmoney_single_reporter_list_all_path)
        for pageNo in tqdm(range(1, list_get_data_pageNo_max + 1)):
            list_get_url = f"https://reportapi.eastmoney.com/report/list?pageSize=100&beginTime=2000-09-26&endTime=2024-11-24&pageNo={pageNo}&qType=1"
            response = self._request_get(url=list_get_url)
            try:
                data = json.loads(response.text)['data']
            except Exception as e:
                print(e, pageNo)
            try:
                with open(eastmoney_single_reporter_list_all_path, 'a', encoding='utf8') as f:
                    for data_item in data:
                        f.write(json.dumps(data_item, ensure_ascii=False) + '\n')
            except Exception as e:
                print(e, pageNo)

    def download_single_reporter_all(self):
        single_reporter_list_path = './data/eastmoney_single_reporter_list_all.json'
        single_reporter_list = self._load_json_list(single_reporter_list_path)
        for single_reporter in tqdm(single_reporter_list):
            infoCode = single_reporter['infoCode']
            if os.path.exists(f'/data/jinsong/data/FinRpt/dataset/data/eastmoney_single_reporter_pdf/{infoCode}.pdf'):
                continue
            single_reporter_url = f'https://data.eastmoney.com/report/info/{infoCode}.html'
            response = self._request_get(single_reporter_url)
            try:
                page = etree.HTML(response.text)
            except Exception as e:
                print(e, infoCode)
                continue
            try:
                report_content = page.xpath('//*[@id="ContentBody"]/div[@class="newsContent"]')[0]
                report_paragraphs = []
                for item in report_content:
                    if item.tag == 'p':
                        item_text = item.text.strip()
                        if len(item_text) > 0:
                            report_paragraphs.append(item_text)
            except Exception as e:
                print(e, infoCode)
            try:
                pdf_url = page.xpath('/html/body/div[1]/div[7]/div[4]/div[1]/div[1]/div[1]/div/span[5]/a')
                pdf_save_path = f'/data/jinsong/data/FinRpt/dataset/data/eastmoney_single_reporter_pdf/{infoCode}.pdf'
                if len(pdf_url) > 0 and not os.path.exists(pdf_save_path):
                    pdf_url = pdf_url[0].attrib['href']
                    pdf_response = self._request_get(pdf_url)
                    with open(pdf_save_path, 'wb') as f:
                        f.write(pdf_response.content)
            except Exception as e:
                print(e, infoCode)
            single_reporter['report_paragraphs'] = report_paragraphs
            try:
                with open(f'./data/eastmoney_single_reporter_all.json', 'a', encoding='utf8') as f:
                    f.write(json.dumps(single_reporter, ensure_ascii=False) + '\n')
            except Exception as e:
                print(e, infoCode)
    
    def download_industry_reporter_all(self):
        industry_reporter_list_path = './data/eastmoney_industry_reporter_list_all.json'
        industry_reporter_list = self._load_json_list(industry_reporter_list_path)
        if not os.path.exists('/data/jinsong/FinRpt/dataset/data/eastmoney_industry_reporter_pdf'):
            os.makedirs('/data/jinsong/FinRpt/dataset/data/eastmoney_industry_reporter_pdf')
        for industry_reporter in tqdm(industry_reporter_list):
            infoCode = industry_reporter['infoCode']
            if os.path.exists(f'/data/jinsong/FinRpt/dataset/data/eastmoney_industry_reporter_pdf/{infoCode}.pdf'):
                continue
            industry_reporter_url = f'https://data.eastmoney.com/report/zw_industry.jshtml?infocode={infoCode}'
            response = self._request_get(industry_reporter_url)
            try:
                page = etree.HTML(response.text)
            except Exception as e:
                print(e, infoCode)
                continue
            try:
                report_content = page.xpath('//div[@class="ctx-content"]')[0]
                report_paragraphs = []
                for item in report_content:
                    if item.tag == 'p':
                        item_text = item.text
                        if item_text is None:
                            item_text = ''
                        if len(item_text) > 0:
                            report_paragraphs.append(item_text)
            except Exception as e:
                print(e, infoCode)
            try:
                pdf_url = page.xpath('//a[@class="pdf-link"]')
                pdf_save_path = f'/data/jinsong/FinRpt/dataset/data/eastmoney_industry_reporter_pdf/{infoCode}.pdf'
                if len(pdf_url) > 0 and not os.path.exists(pdf_save_path):
                    pdf_url = pdf_url[0].attrib['href']
                    pdf_response = self._request_get(pdf_url)
                    with open(pdf_save_path, 'wb') as f:
                        f.write(pdf_response.content)
            except Exception as e:
                print(e, infoCode)
            industry_reporter['report_paragraphs'] = report_paragraphs
            try:
                with open(f'/data/jinsong/FinRpt/dataset/data/eastmoney_industry_reporter_all.json', 'a', encoding='utf8') as f:
                    f.write(json.dumps(industry_reporter, ensure_ascii=False) + '\n')
            except Exception as e:
                print(e, infoCode)



if __name__ == "__main__":
    eastmoney = Eastmoney_Streaming({'max_retry': 5})
    # eastmoney.download_single_reporter_list_all()
    eastmoney.download_single_reporter_all()
    # eastmoney.download_industry_reporter_list_all()
    # eastmoney.download_industry_reporter_all()
