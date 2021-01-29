import argparse
import asyncio
import hashlib
import json
import os
import shutil
import time
import urllib
import uuid

import pyppeteer
import requests

import exceptions
from flatten import flatten

browser = None
prefix = 'https://instagram.com'
abspath = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Scrape all media from a public Instagram account and print their links/ download it all')
    parser.add_argument('-u', '--username', required=True, type=str,
                        help="(Public) Instagram account handle (e.g 'apple')")
    parser.add_argument('-p', '--path', type=str,
                        default=f'{abspath}/media', help=f'Path to download media into. Defaults to {abspath}/media/[user] or {abspath}/media')
    parser.add_argument('--save', type=str, choices=['text', 'media', 'none'], default='media',
                        help=f"Info saving mode. Uses path provided on --path or default ('{abspath}/media' if --save is 'text' else '{abspath}/media/[user]'). 'text' creates a text file with the links; 'media' downloads the files; 'none' prints the links on terminal. Default: 'media'")
    parser.add_argument('-e', '--email', type=str, default='',
                        help="Your account's email address or username")
    parser.add_argument('-s', '--secret', type=str, default='',
                        help="Your account's password")
    parser.add_argument('-n', '--naming', choices=['unique', 'sequential', 'original'], default='sequential',
                        type=str, help="File saving method. Ignored completely if --save is not set to 'media'")
    parser.add_argument('---not-headless', nargs='?', default=False, help='Controls Chromium (used by `pyppeteer`) headlesness.')
    args = parser.parse_args()

    return args.username, f'{args.path}/{args.username}' if args.save == 'media' else args.path, args.save, args.naming, args.email, args.secret, args.not_headless


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

    time.sleep(10)
    await page.close()
    log('logged in', 'log', False)


async def block_popup(page):
    try:
        await page.evaluate("() => document.querySelectorAll('.RnEpo, ._Yhr4').forEach(el => el.setAttribute('style', 'display: none !important'))")
    except:
        pass


async def scroll_and_fetch(page):
    async def parse_triplet(triplet):
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
                url = await main.querySelectorEval('video', 'm => m.src')
                if 'blob' in url:
                    continue

                urls.append(url)
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

    return [await parse_triplet(triplet) for triplet in triplets.values()]


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

    def save_media(url, count):
        if not save_mode == 'media':
            if save_mode == 'text':
                with open(f'{path}/{user}.txt', 'a') as f:
                    f.write(f'{url}\n')
            else:
                print(url)
        else:
            parsed_url = urllib.parse.urlparse(url)
            # if parsed_url.scheme == 'blob':
                # print('blob scheme here!', url)
            # else:
            r = requests.get(url, stream=True)
            if not r.ok:
                raise exceptions.MediaRetrievalError(r.reason)

            r.raw.decode_content = True
            name = ''

            if naming == 'unique':
                name = uuid.uuid4()
            elif naming == 'sequential':
                name = count
            elif naming == 'original':
                name = os.path.splitext(parsed_url.path)[0].split('/')[-1]

            with open(f"{path}/{name}{os.path.splitext(parsed_url.path)[1]}", 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    user, path, save_mode, naming, email, password, not_headless = parse_args()
    login_info = {}
    if email and password:
        login_info['email'], login_info['password'] = email, password
    elif email != '' or password != '':
        log('ignoring login info completely', 'warn', False)

    browser = await pyppeteer.launch({'headless': False if not_headless == None else True})
    page = await browser.newPage()

    try:
        if login_info:
            await login(login_info)

        await page.goto(f'{prefix}/{user}')
        body = await page.evaluate('() => document.body.textContent')
        if "Sorry, this page isn't available." in body:
            raise exceptions.InvalidUsernameError()
        elif 'This Account is Private' in body:
            raise exceptions.PrivateAccountError()

        await page.evaluate("() => document.body.setAttribute('style', 'overflow: auto !important;')")
        await block_popup(page)

        urls = flatten(await scroll_and_fetch(page), str)
        if not save_mode == 'none' and not os.path.isdir(path):
            os.makedirs(path)

        [save_media(urls[i], i + 1) for i in range(len(urls))]

    except Exception as e:
        log(getattr(e, 'message', repr(e)), 'error')


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
