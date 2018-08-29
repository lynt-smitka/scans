#!/usr/bin/python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from urllib.parse import urlsplit

def test(url):

        furl = "http://{0}/.git/HEAD".format(url)
        agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36 Lynt.cz'}
        
        http = urllib3.PoolManager()
        timeout = urllib3.Timeout(connect=5.0, read=10.0)
        
        r = http.request('GET', furl, headers=agent, timeout=timeout)
        print("TEST: {0}".format(furl))
        
        try: 
          if r.status == 200 and 'ref: refs' in r.data.decode('utf-8'):
            finalurl = furl
            if(r.retries.total<3):
              finalurl=((r.retries.history[-1].redirect_location))
            
            base_url = "{0.scheme}:__{0.netloc}".format(urlsplit(finalurl))
            #<save result base_url>

        except Exception as e:
          print(vars(e))

        r = None


#urls = <get the url list>

print("Start!")

with ThreadPoolExecutor(max_workers=100) as executor:
          results = executor.map(test, urls)

print("Done!")
