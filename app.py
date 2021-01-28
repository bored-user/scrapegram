import argparse
import asyncio
import hashlib
import json
import os
import time

import pyppeteer

import exceptions
from flatten import flatten

browser = None
prefix = 'https://instagram.com'
abspath = os.path.dirname(os.path.abspath(__file__))


def parse_args(login):
    parser = argparse.ArgumentParser(
        description='Scrape all media from a public Instagram account and print their links/ download it all')
    parser.add_argument('-u', '--username', required=True, type=str,
                        help="(Public) Instagram account handle (e.g 'apple')")
    parser.add_argument('-d', '--download', default='False', type=str,
                        help="'True' downloads all media to the path specified on '-p'. 'False' only prints links on the terminal")
    parser.add_argument('-p', '--path', type=str,
                        default=f'{abspath}/downloads/[[[user]]]', help='Path to download media into. Defaults to $PWD/downloads/[user]')
    parser.add_argument('-e', '--email', type=str, default='',
                        help="Email address or username (in order to login & access private accounts of people you're following)")
    parser.add_argument('-s', '--secret', type=str, default='',
                        help="Your account's password (in order to login & access private accounts of people you're following)")
    args = parser.parse_args()

    try:
        assert args.download == 'False' or args.download == 'True'
    except AssertionError:
        log("-d must be either 'True' or 'False'", 'error')

    if args.email and args.secret:
        login['email'], login['password'] = args.email, args.secret
    elif args.email != '' or args.secret != '':
        log('ignoring login info completely', 'warn', False)

    return args.username, args.download, args.path.replace('[[[user]]]', args.username)


def log(msg: str, type: str, quit: bool = True):
    print(f'app.py: {type}: {msg.lower()}')

    if quit:
        exit(1)


async def login(info: dict):
    page = await browser.newPage()

    await page.goto(f'{prefix}/accounts/login')
    await (await wait_loading('input[name=username]', page)).type(info['email'])
    await (await wait_loading('input[name=password]', page)).type(info['password'])
    await (await wait_loading('button[type=submit]', page)).click()

    with open(f'{abspath}/config.json', 'w') as f:
        json.dump(info, f)

    # await wait_loading('nav', page)
    time.sleep(10)
    await page.close()
    log('logged in', 'log', False)


async def block_popup(page):
    try:
        await page.evaluate("() => document.querySelectorAll('.RnEpo, ._Yhr4').forEach(el => el.setAttribute('style', 'display: none !important'))")
    except:
        pass


async def scroll_and_fetch(page):
    async def parse_triplets(triplet):
        urls = []

        for media in await triplet.querySelectorAll('.v1Nh3.kIKUG._bz0w'):
            page = await browser.newPage()
            await page.goto(await media.querySelectorEval('a', 'a => a.href'))

            main = await page.querySelector('article')
            presentation = await main.querySelector('div[role=presentation]')
            video = await main.querySelector('video')
            photo = await main.querySelector('.FFVAD')

            if presentation:
                for media in await presentation.querySelectorAll('ul li'):
                    if await page.evaluate('m => m.children.length == 0', media):
                        continue

                    urls.append(await media.querySelectorEval('.FFVAD' if await media.querySelector('.FFVAD') else 'video', 'm => m.src'))
            elif video:
                urls.append(await main.querySelectorEval('video', 'm => m.src'))
            elif photo:
                urls.append(await main.querySelectorEval('.FFVAD', 'm => m.src'))

            await page.close()

        return urls

    triplets = {}
    await wait_loading('.Nnq7C.weEfm', page)
    posts = await page.querySelectorEval('main header section ul li', "l => Number(l.textContent.replace(/[^0-9]/g, ''))")

    while True:
        shown_triplets = await page.querySelectorAll('.Nnq7C.weEfm')
        await page.screenshot({'path': 'realtime.png'})

        for triplet in shown_triplets:
            md5 = hashlib.md5((await page.evaluate('t => t.innerHTML', triplet)).encode()).hexdigest()

            if md5 in triplets:
                continue
            triplets[md5] = triplet

        await page.evaluate('t => t.scrollIntoView(false)', shown_triplets[-1])
        await block_popup(page)

        if len(triplets) * 3 >= posts:
            break

    await page.close()
    return [await parse_triplets(triplet) for triplet in triplets.values()]


async def wait_loading(query, page):
    element = await page.querySelector(query)

    while element == None:
        await page.screenshot({'path': 'realtime.png'})
        element = await page.querySelector(query)
        time.sleep(0.1)

    await page.screenshot({'path': 'realtime.png'})
    return element


async def main():
    global browser
    _login = {}
    user, download, path = parse_args(_login)

    browser = await pyppeteer.launch({'headless': False})
    page = await browser.newPage()

    try:
        if _login:
            await login(_login)

        await page.goto(f'{prefix}/{user}')

        body = await page.evaluate('() => document.body.textContent')
        if "Sorry, this page isn't available." in body:
            raise exceptions.InvalidUsernameError()
        elif 'This Account is Private' in body:
            raise exceptions.PrivateAccountError()
    except Exception as e:
        log(getattr(e, 'message', repr(e)), 'error')

    await page.evaluate("() => document.body.setAttribute('style', 'overflow: auto !important;')")
    await block_popup(page)
    urls = flatten(await scroll_and_fetch(page), str)
    print(urls)
    print(len(urls))


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
