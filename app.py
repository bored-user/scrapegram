import argparse
import asyncio
import os

import pyppeteer

import exceptions


def parse():
    parser = argparse.ArgumentParser(
        description='Scrape all media from a public Instagram account and print their links/ download it all')
    parser.add_argument('-u', '--username', required=True, type=str,
                        help="(Public) Instagram account handle (e.g 'apple')")
    parser.add_argument('-d', '--download', default='False', type=str,
                        help="'True' downloads all media to the path specified on '-p'. 'False' only prints links on the terminal")
    parser.add_argument('-p', '--path', type=str,
                        default=f'{os.path.dirname(os.path.abspath(__file__))}/downloads', help='Path to download media into. Defaults to $PWD/downloads')
    args = parser.parse_args()

    try:
        assert args.download == 'False' or args.download == 'True'
    except AssertionError:
        error("-d must be either 'True' or 'False'")

    return args.username, args.download, args.path


def error(msg):
    print(f'app.py: error: {msg}')
    exit(1)


async def main():
    user, download, path = parse()

    browser = await pyppeteer.launch()
    page = await browser.newPage()

    await page.setViewport({'width': 1920, 'height': 1080})

    try:
        await page.goto(f'https://www.instagram.com/{user}')
        body = await page.evaluate('() => document.body.textContent')

        if 'Sorry, this page isn\'t available.' in body:
            raise exceptions.InvalidUsernameError()
        elif 'This Account is Private' in body:
            raise exceptions.PrivateAccountError()
    except Exception as e:
        error(getattr(e, 'message', repr(e)))

    await page.evaluate("() => document.body.setAttribute('style', 'overflow: auto !important;')")
    await page.evaluate("() => document.querySelector('.RnEpo, ._Yhr4').forEach(el => el.setAttribute('display: none !important'))")


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
