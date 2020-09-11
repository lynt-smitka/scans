#!/usr/bin/python3
import asyncio
from aiohttp import ClientSession
from aiohttp import ClientTimeout


async def fetch(url, session):

    furl = "http://{0}/.git/HEAD".format(url)
    agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
       
    try:
      async with session.get(furl, headers=agent, compress=True) as r:
        print("TEST: {0}".format(furl))
        with open('last.log', 'w') as the_file:
          the_file.write(furl)
        if r.status == 200 and 'ref: refs' in str(r.content._buffer):
          base_url = "{0}__{1}".format(r._url.scheme,r._url.host)
          #<save result base_url>
        r=None  
    except Exception as e:
      print(vars(e))


async def sem_fetch(sem, url, session):
    async with sem:
        await fetch(url, session)

async def run(urls):
    
    tasks = []
    sem = asyncio.Semaphore(10000)
    timeout = ClientTimeout(sock_connect=5.0, sock_read=20.0)
    async with ClientSession(timeout = timeout) as session:
        for url in urls:
            task = asyncio.ensure_future(sem_fetch(sem, url, session))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)


chunks_size = 100000

#urls = <get the url list>

print("Start!")
chunks = [urls[x:x+chunks_size] for x in range(0, len(urls), chunks_size)]

for chunk in chunks:
    print("Start chunk")
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(chunk))
    loop.run_until_complete(future)
    print("End chunk")

print("Done!")
