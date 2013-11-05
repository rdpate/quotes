#encoding: utf-8
# http://peterlevi.com/variety/wiki/Writing_plugins

import os
import logging
import subprocess
from variety.plugins.IQuoteSource import IQuoteSource

logger = logging.getLogger("variety")

mdash = u"—"

def text_replacements(s):
  s = s.replace(u" -- ", mdash)
  s = s.replace(u"...", u"…")
  return s

class FortuneSource(IQuoteSource):
  @classmethod
  def get_info(cls):
    return {
      "name": "Fortune",
      "description": "Runs fortune.",
      #"author": "",
      #"version": "",
      }

  def get_random(self):
    try:
      lines = subprocess.check_output(["fortune", "--no-wrap", "--qa-only", "-n100"])
    except subprocess.CalledProcessError:
      return []

    # parses my personal fortune's output
    lines = lines.rstrip().decode("utf-8").split("\n")
    results = []
    while len(lines) >= 2:
      q, a, lines = lines[0], lines[1][5:], lines[2:]
      q = text_replacements(q)
      if a == "(unknown)":
        a = None
      else:
        a = "%s %s" % (mdash, a)
      results.append({
        "quote": q,
        "author": a,
        })

    return results
