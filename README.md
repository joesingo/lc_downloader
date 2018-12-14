# lc_downloader

Small Python 3 script to download learning materials from [Learning
Central](https://learningcentral.cf.ac.uk) for Cardiff University.

Install requirements with `pip3 install -r requirements.txt`.

Unfortunately this does not deal with authenticating with Learning Central via
the Cardiff single sign-on. Instead, log in via the usual methods and find the
value of the `s_session_id` cookie to get your session ID (e.g. in Chrome:
developer console -> application -> cookies -> learningcentral.cf.ac.uk).

Usage:
```
python3 download.py SESSION_ID MODULE_NAME OUTPUT_DIR
```

`MODULE_NAME` only needs to be a sub-string of the full module name (which
includes module code and year), and is case insensitive. The directory and file
names as given on LC are preserved, and all files are written under
`OUTPUT_DIR`.
