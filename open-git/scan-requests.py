#!/usr/bin/python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urlsplit

def test(web):

        furl = "http://{0}/.git/HEAD".format(url)
        agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
 
        r = requests.get(furl, timeout=5, allow_redirects=True, headers=agent, verify=False)
        print("TEST: {0}".format(furl))
        
        try: 
          if r.status_code == 200 and 'ref: refs' in r.text:
            base_url = "{0.scheme}:__{0.netloc}".format(urlsplit(r.url))
            #<save result base_url>

        except Exception as e:
          print(vars(e))

        r = None


#urls = <get the url list>

print("Start!")

with ThreadPoolExecutor(max_workers=300) as executor:
          results = executor.map(test, urls)

print("Done!")
