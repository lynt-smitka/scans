import re
import asyncio
import aiohttp
import aiomysql
from asyncio import Queue
from aiohttp import ClientSession
from aiohttp import TCPConnector
from urllib.parse import urlparse
from aiomysql import Pool


class Sentinel():
    pass


STOP = Sentinel()
WORKERS = 500
QUEUE_SIZE = 20000


def normalize_url(url):
    if 'http' not in url:
        url = "http://" + url
    parsed_uri = urlparse(url)
    return '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)


async def fetch(data, session, pool):
    agent = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}

    version = None
    theme = None
    plugins = list()
    version_ok = 0
    web_id = data[0]
    furl = normalize_url(data[1])
    print("TEST: " + furl)
    try:

        async with session.get(furl, headers=agent, compress=True, verify_ssl=False) as response:

            r = await response.text()

            # Version

            if "content=\"WordPress " in r:
                match = re.search("content=\"WordPress ([0-9\.]+)", r, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    version_ok = 1

            # Theme

            if "/wp-content/themes/" in r:
                match = re.search("\/wp-content\/themes\/([a-zA-Z0-9-_\.]+)\/", r, re.IGNORECASE)
                if match:
                    theme = match.group(1)

            # Plugins

            if "/wp-content/plugins/" in r.text:
                match = re.findall("\/wp-content\/plugins\/([a-zA-Z0-9-_\.]+)\/", r.text, re.IGNORECASE)
                uniq = list(set(match))
            for plugin in uniq:
                plugins.append(plugin)

        if not version_ok:
            async with session.get(furl + "/wp-admin/install.php", headers=agent, compress=True, verify_ssl=False,
                                   timeout=20.0) as response:
                r = await response.text()
                if "install.min.css?ver=" in r:
                    match = re.search("install\.min\.css\?ver=([0-9\.]+)", r, re.IGNORECASE)
                    if match:
                        version = match.group(1)
                        version_ok = 1

        if not version_ok and "https://" in furl:
            async with session.get(furl.replace("https://", "http://") + "/wp-admin/install.php", headers=agent,
                                   compress=True, verify_ssl=False, timeout=20.0) as response:
                r = await response.text()

                if "install.min.css?ver=" in r:

                    match = re.search("install\.min\.css\?ver=([0-9\.]+)", r, re.IGNORECASE)
                    if match:
                        version = match.group(1)
                        version_ok = 1

        if not version_ok:
            async with session.get(furl + "/feed", headers=agent, compress=True, verify_ssl=False,
                                   timeout=20.0) as response:
                r = await response.text()

                if "<generator>" in r and "//wordpress.org/?v" in r:
                    match = re.search("\/\/wordpress.org\/\?v=([0-9\.]+)", r, re.IGNORECASE)

                    if match:
                        version = match.group(1)
                        version_ok = 1

        if not version_ok:
            async with session.get(furl + "/index.php?feed=rss", headers=agent, compress=True, verify_ssl=False,
                                   timeout=20.0) as response:
                r = await response.text()

                if "<generator>" in r and "//wordpress.org/?v" in r:
                    match = re.search("\/\/wordpress.org\/\?v=([0-9\.]+)", r, re.IGNORECASE)

                    if match:
                        version = match.group(1)
                        version_ok = 1

        if version_ok:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("UPDATE webs SET version = %s, theme = %s, lastcheck = NOW() WHERE web_id=%s",
                                      (version, theme, web_id))
                    for plugin in plugins:
                        await cur.execute("INSERT INTO plugins (web, plugin) VALUES(%s,%s)", (web_id, plugin))
                    await conn.commit()


    except (aiohttp.ServerTimeoutError, TimeoutError, asyncio.TimeoutError):
        print("Timeout")

    except aiohttp.ClientResponseError:
        print("Response error")

    except Exception as e:
        print(vars(e))


async def producent(queue: Queue, pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            num = await cur.execute("SELECT id, final_url from webs where wp=1")
            items = await cur.fetchall()
            for row in items:
                await queue.put(row)

    for _ in range(WORKERS):
        await queue.put(STOP)


async def consument(queue: Queue, session, pool: Pool):
    while True:
        item = await queue.get()
        if item is STOP:
            break
        await fetch(item, session, pool)
        queue.task_done()


async def run_tasks(queue: Queue, session, pool: Pool):
    consuments = [asyncio.ensure_future(consument(queue, session, pool)) for _ in range(WORKERS)]
    await producent(queue, pool)
    await asyncio.gather(*consuments)


async def main():
    queue = Queue(maxsize=QUEUE_SIZE)

    async with aiomysql.create_pool(host='####', port=3306,
                                    user='####', password='####',
                                    db='####', loop=asyncio.get_running_loop()) as pool:
        conn = TCPConnector(ttl_dns_cache=3600, limit=1000)
        async with ClientSession(connector=conn, raise_for_status=False, read_timeout=20.0,
                                 conn_timeout=5.0) as session:
            await run_tasks(queue, session, pool)


if __name__ == "__main__":
    asyncio.run(main())
