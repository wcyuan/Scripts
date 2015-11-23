#!/usr/bin/env python2
# entry of program,
# modified from
# https://github.com/kuchaguangjie/pygtrans/blob/master/main.py

# ----------------------------------------------------------------------- #

import fileinput
from os.path import expanduser
import sys
import urllib

try:
  import ConfigParser as configparser
except ImportError:
  from six.moves import configparser

try:
  import urllib2
except ImportError:
  import urllib.request as urllib2

try:
  sys.path.append(expanduser("~/code/pkgs/beautifulsoup4-4.3.2/"))
  from BeautifulSoup import BeautifulSoup
except ImportError:
  from bs4 import BeautifulSoup

# ----------------------------------------------------------------------- #

version = "v0.1" + " beta5"
DEFAULT_GOOGLE_DOMAIN = "google.com"
DEFAULT_TARGET_LANG = "en"
DEFAULT_SRC_LANG = "auto"

# ----------------------------------------------------------------------- #


def main():
  #(googleDomain, targetLang, srcLang) = read_config()
  #(targetLang, srcLang, key) = read_args(targetLang, srcLang)
  (googleDomain, targetLang, srcLang) = (DEFAULT_GOOGLE_DOMAIN,
                                         DEFAULT_TARGET_LANG, DEFAULT_SRC_LANG)
  for (ii, line) in enumerate(fileinput.input()):
    line = line.rstrip()
    page = send_request(line,
                        googleDomain=googleDomain,
                        srcLang=srcLang,
                        targetLang=targetLang)
    result = parse_response(page)
    #print(unicode(key, "utf-8") + "\t->\t" + result)
    print ii, "orig :", line
    print ii, "trans:", result.encode("utf-8")

# ----------------------------------------------------------------------- #


def read_config():
  googleDomain = DEFAULT_GOOGLE_DOMAIN
  targetLang = DEFAULT_TARGET_LANG
  srcLang = DEFAULT_SRC_LANG

  home = expanduser("~")
  config = configparser.RawConfigParser()
  config.read(home + "/.config/pygtrans/config.ini")

  if config.has_option("basic", "google_domain"):
    tmpDomain = config.get("basic", "google_domain")
    if tmpDomain and (not tmpDomain.isspace()):
      googleDomain = tmpDomain

  if config.has_option("basic", "target_language"):
    tmpTargetLang = config.get("basic", "target_language")
    if tmpTargetLang and (not tmpTargetLang.isspace()):
      targetLang = tmpTargetLang

  if config.has_option("basic", "source_language"):
    tmpSrcLang = config.get("basic", "source_language")
    if tmpSrcLang and (not tmpSrcLang.isspace()):
      srcLang = tmpSrcLang
  return (googleDomain, targetLang, srcLang)


def read_args(targetLang, srcLang):
  ## param check
  key = ""
  if len(sys.argv) < 2:
    print("Please use following formats:\n\t%s" %
          ("pygtrans <input_string> [<target_language>] [<source_language>]"))
    print("\t%s" % ("pygtrans (-v | --version)"))
    print("Common languages:\n\t%s\n" % ("en, zh, zh_TW, ja, fr, de,"))
    sys.exit(1)
  elif sys.argv[1] == "-v" or sys.argv[1] == "--version":
    print("pygtrans - " + version)
    sys.exit(0)
  else:
    key = sys.argv[1]
    if len(sys.argv) >= 3:
      targetLang = sys.argv[2]
    if len(sys.argv) >= 4:
      srcLang = sys.argv[3]
  return (targetLang, srcLang, key)


def send_request(text,
                 googleDomain=DEFAULT_GOOGLE_DOMAIN,
                 srcLang=DEFAULT_SRC_LANG,
                 targetLang=DEFAULT_TARGET_LANG):
  ## http request
  userAgent = ("Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like "
               "Gecko) Chrome/39.0.2171.95 Safari/537.36")
  headers = {"User-Agent": userAgent}
  url = ("http://translate." + googleDomain + "/?" +
         urllib.urlencode({"langpair": "|".join((srcLang, targetLang)),
                           "text": text}))
  return urllib2.urlopen(urllib2.Request(url, None, headers))


def parse_response(page):
  resultId = "result_box"
  ## result parse
  soup = BeautifulSoup(page)
  return soup.body.find(id=resultId).text

# ----------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# ----------------------------------------------------------------------- #
