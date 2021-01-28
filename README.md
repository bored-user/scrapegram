# scrapegram

Python Instagram scraping application.

### Usage

One must provide a username using the `-u` (`--username`) flag. That's the only mandatory argument.
```shell
$ python3 app.py -u apple
```

Optional arguments:
* `--save`:
    - `media`: downloads all photo/ video on the specified `--path` location (*default*)
    - `text`: will save a text file (on `--path` location) with the links
    - `none`: will only echo out each link on the terminal
* `-p` (`--path`): Specifies the path where the media will be saved into (defaults to `$PWD/media/[username]` if `--save` is set to `media`, else `$PWD/media/[username].txt`).
* `-n` (`--naming`):
    - `unique`: uses `uuid.uuid4()` to generate the file names
    - `sequential`: results in `1.[ext]`, `2.[ext]`, `3.[ext]`, etc. (where `[ext]` is the original file's extension) (*default*)
    - `original`: uses the original Instagram server-stored file name
* `-e` (`--email`): Email of an Instagram account (to log in to and view private-followed-by-the-given-account accounts).
* `-s` (`--secret`): Password of an Instagram account (to log in to and view private-followed-by-the-given-account accounts).
* `---not-headless`: Shows the Chromium window (used by `pyppeteer`). Makes it easier to debug.


Examples:
```shell
$ python3 app.py -u apple --save media -p /home # downloads all files on /home
$ python3 app.py -u apple --save text -p /home # creates /home/apple.txt and writes the output there
$ python3 app.py -u apple # downloads all files on $PWD/media/apple/
$ python3 app.py -u apple --save text # saves all links on $PWD/media/apple.txt
$ python3 app.py -u dexter -e morgan.debra@mmpd.us -s FUCKING PASSWORD # logs into morgan.debra@mmpd.us using FUCKINGPASSWORD as password and downloads Dexter's secrete & private pics & vids.
```

### Dependencies

`requirements.txt` has all the dependencies needed. Install them by running `pip install -r requirements.txt` on your terminal.

### .venv

I uploaded my `.venv` folder with the source code (as one can see above). Therefore, it's much easier to just run `source ./bin/activate` (before `$ python3 app.py`) instead of downloading the modules manually - because they'll be already installed on the virtual enviroment.

### P.S.

1. Obviously, `--save none` is much faster than the other two - since it doesn't have to write/ download and additional file.
2. I'd like to left it noted the fact that it's harder and harder for the script to work 100% with no login. You can try, but I can't garantee. Tip: open `realtime.png` image (that will be generated while the script is running) and keep refreshing it to see what's going on. If you see a big "ERROR - Try again later" message on the Instagram page, it failed.
3. Errors will be thrown if one tries to access a private account (if you can't view it).
4. Errors will be thrown if one inputs an unexistant user.
5. Your login credentials are saved on `config.json` (which is generated while the script is running). Don't worry! It's not uploaded anywhere, it's just on your computer (read the source code if you don't believe me)
6. `requirements.txt` has all the dependencies needed. Install them by running `pip install -r requirements.txt` on your terminal.
7. I noticed that the chance of the "Try again later" error occurring is smaller if the browser window is being displayed. See `---not-headless` on optional arguments above.
8. If you'd like to test the application, I sugest `python3 app.py -u deepikapakudone ---not-headless`. `deepikapakudone` is a public account with only 7 posts (until now, at least). Btw, that's not sponsoring or advertisement. It's just an account I found when searching accounts with small number of posts to guess what? Exactly, test the application while I was developing it.
