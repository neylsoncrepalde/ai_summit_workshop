import os
import boto3
from urllib.request import urlopen
from bs4 import BeautifulSoup

s3_client = boto3.client('s3')
BUCKET_NAME = 'ai-summit-workshop'
TARGET_FOLDER = "competency-data"


def get_article(url, target_folder):
    html = urlopen(url).read()
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get article's text
    article = soup.find('article')
    text = article.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    root_filename = url[51:-26]
    with open(f'{target_folder}/{root_filename}.txt', 'w') as f:
        f.write(text)
    
    return(True)


def upload_to_s3(local_file, s3_file):
    s3_client.upload_file(local_file, BUCKET_NAME, s3_file)

files = [
    "https://apn-checklists.s3.amazonaws.com/competency/education/consulting/Ccf_WVoOo.html",
    "https://apn-checklists.s3.amazonaws.com/competency/energy/consulting/CTpftZxbZ.html",
    "https://apn-checklists.s3.amazonaws.com/competency/financial-services/consulting/CWNIstW4j.html",
    "https://apn-checklists.s3.amazonaws.com/competency/conversational-ai/consulting/Cvkq1FdL1.html",
    "https://apn-checklists.s3.amazonaws.com/competency/data-and-analytics/consulting/CwDeMHw3L.html",
    "https://apn-checklists.s3.amazonaws.com/competency/devops/consulting/Cm5yq5ehT.html",
    "https://apn-checklists.s3.amazonaws.com/competency/machine-learning/consulting/CDrF84yod.html",
    "https://apn-checklists.s3.amazonaws.com/competency/security/consulting/CXLOf6Hk3.html"
]

if __name__ == "__main__":
    os.makedirs(TARGET_FOLDER, exist_ok=True)
    
    for url in files:
        get_article(url, TARGET_FOLDER)
    
    for file in os.listdir(TARGET_FOLDER):
        upload_to_s3(os.path.join(TARGET_FOLDER, file), "kb-competency/"+file)
