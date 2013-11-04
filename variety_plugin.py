# http://peterlevi.com/variety/wiki/Writing_plugins

import os
import logging
import subprocess
from variety.plugins.IQuoteSource import IQuoteSource

logger = logging.getLogger("variety")

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
      q = subprocess.check_output(["fortune", "--no-wrap"])
    except subprocess.CalledProcessError:
      return []

    # parses my personal fortune's output
    q, _, author = q.rpartition("\n  -- ")
    if author:
      author, _, _ = author.partition(" [")
    if author == "(unknown)":
      author = None

    return [{
      "quote": q,
      "author": author,
      "sourceName": None,
      "link": None,
      }]
