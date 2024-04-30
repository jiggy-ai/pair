"""
Extract readable text from a URL via various hacks
"""

from loguru import logger
from bs4 import BeautifulSoup, NavigableString, Tag
from readability import Document    # https://github.com/buriy/python-readability
import requests
import urllib.parse
import json
import re


from github_api import github_readme_text
from pdf_text import pdf_text
from exceptions import *
from retry import retry
    
user_agent = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"

headers = {'User-Agent': user_agent}

def extract_text_from_html(content):
    soup = BeautifulSoup(content, 'html.parser')

    blacklist = ['[document]','noscript','header','html','meta','head','input','script', "style"]
    # there may be more elements we don't want

    output =  ""      
    for t in soup.find_all(text=True):
        if t.parent.name not in blacklist:
            output += '{} '.format(t)
    return output

def get_language(html):
    soup = BeautifulSoup(html, 'html.parser')
    try:
        return soup.html["lang"]
    except:
        return ""

@retry(tries=5)    
def get_url_text(url):
    """
    get url content and extract readable text
    returns the text
    """
    resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code != 200:
        logger.warning(url)
        raise NetworkError(f"Unable to get URL ({resp.status_code})")

    CONTENT_TYPE = resp.headers['Content-Type']

    if 'json' in CONTENT_TYPE:
        return str(resp.content), "", ""
    
    if 'pdf' in CONTENT_TYPE:
        text, title, language = pdf_text(resp.content)
        return text, title, language    
    
    if "html" not in CONTENT_TYPE:
        logger.warning(url)
        raise UnsupportedContentType(f"Unsupported content type: {resp.headers['Content-Type']}")

    language = get_language(resp.text)
    logger.info(f"language: {language}")
        
    doc = Document(resp.text)
    title = doc.title()
    text = extract_text_from_html(doc.summary())

    if not len(text) or text.isspace():
        logger.warning(url)
        raise EmptyText("Unable to extract text data from url")
    return text, title, language



def url_to_text(url):
    #logger.info("url_to_text: "+url)
    HOPELESS = ["youtube.com",
                "www.youtube.com"]
    if urllib.parse.urlparse(url).netloc in HOPELESS:
        logger.warning(url)        
        raise UnsupportedHostException("Unsupported host: {urllib.parse.urlparse(url).netloc}")

    if urllib.parse.urlparse(url).netloc == 'github.com':
        # for github repos use api to attempt to find a readme file
        text, title = github_readme_text(url)
        language = 'en'  # XXX  dynamically determine language
    else:
        text, title, language = get_url_text(url)

    #logger.debug("url_to_text: "+text)
    return text, title, language




def extract_filename_code_blocks(text):
    #pattern = r"(?:\*\*(\S+)\*\*|##\s*(\S+))?\s*```(\w+)?(?:\s+)?(.*?)```"
    pattern = r"(?:\*\*(\S+)\*\*:?|##\s*(\S+))?\s*```(\w+)?(?:\s+)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    # Generate tuples (filename, code_block, file_type), handling filename preprocessing
    results = []
    for match in matches:
        # Normalizing filename: match[0] is **filename.ext**, match[1] is ## filename.ext
        filename = match[0] or match[1] or None
        file_type = match[2] if match[2] is not None else 'unknown'  # Set 'unknown' if no file type specified
        code_block = match[3].strip()
        results.append((filename, code_block, file_type))
    
    return results



def extract_code_blocks_with_type(text) -> (str, str):
    pattern = r"```(\w+)?\s*(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [(ftype.strip() if ftype else 'no-type', block.strip()) for ftype, block in matches]


def extract_code_blocks(text) -> str:
    pattern = r"```(?:\w+\s+)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [block.strip() for block in matches]



if __name__ == "__main__":
    import sys
    url = sys.argv[-1]    
    from extract import url_to_text

    text, title, language = url_to_text(url)
    print(text)    
    print(f'language: {language}')
    print(f'Title: {title}')
