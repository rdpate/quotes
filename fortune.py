import glob
import optparse
import random
import re
import textwrap
from collections import namedtuple
from os import path
from pprint import pprint

import yaml


Quote = namedtuple("Quote", ["text", "attribution", "ref", "tags", "notes"])


def main(args):
  optparser = optparse.OptionParser(usage="%prog [OPTION..] [QUOTE FILE..]")
  optparser.add_option("-w", "--width", type="int", default=79)
  optparser.add_option("--max-width", type="int", default=None, help="width = min(width, max_width)")
  optparser.add_option("-v", "--verbose", action="store_true", default=False)
  optparser.add_option("--notes", dest="show_notes", action="store_true", default=False)
  optparser.add_option("--debug", action="store_true", default=False)
  optparser.add_option("--grep", nargs=1, default=None)
  optparser.add_option("--no-wrap", dest="wrap", action="store_false", default=True)
  optparser.add_option("--blank-line", action="store_true", default=False,
    help="output a blank line between each quote")
  optparser.add_option("-1", "--oneline", action="store_true", default=False,
    help="(implies no-wrap)")
  optparser.add_option("--all", action="store_true", default=False,
    help="show all")
  optparser.add_option("-n", type="int", default=None,
    help="run N times")
  opts, args = optparser.parse_args(args)

  if opts.all:
    if opts.n is not None:
      optparser.error("cannot combine --all with -n")
    if opts.grep is not None:
      optparser.error("cannot combine --all with --grep")
  if opts.n is None and opts.grep is None:
    opts.n = 1
  if opts.n is not None and opts.n < 1:
    optparser.error("invalid -n value")

  if opts.max_width:
    opts.width = min(opts.width, opts.max_width)

  if opts.oneline:
    opts.wrap = False

  if opts.verbose:
    opts.show_notes = True

  if args:
    filenames = args
  else:
    filenames = glob.glob(path.join(path.dirname(__file__), "quotes*.yaml"))

  if opts.debug or opts.verbose:
    print "opts:", repr(opts)
    print "args:", repr(args)
    print "filenames:", repr(filenames)
    if opts.debug:
      return

  quotes = []
  for filename in filenames:
    if filename.startswith("-"):
      return "unexpected option"
    collection = path.splitext(path.basename(filename))[0]
    for doc in yaml.load_all(open(filename)):
      q = doc.get("q")
      if "title" in doc:
        a = doc["title"]
      elif "by" in doc:
        a = doc["by"]
        source = doc.get("source")
        if source:
          a += ", " + source
      elif "source" in doc:
        a = doc["source"]
      else:
        a = None

      if "ref" in doc:
        ref = doc["ref"]
        if isinstance(ref, list):
          ref = ", ".join(ref)
      elif "when" in doc:
        ref = str(doc["when"])
      else:
        ref = None

      tags = doc.get("tags", "")

      notes = []
      if "note" in doc:
        notes = doc.get("note")
        if isinstance(notes, basestring):
          notes = [notes]
      assert isinstance(notes, list)

      q = Quote(q, a, ref, tags, notes)
      quotes.append((collection, q))

  if opts.verbose:
    print "[loaded %d quotes from %d files]" % (len(quotes), len(filenames))

  _show_quote_first = [True]
  def show_quote(q, collection):
    if _show_quote_first[0]:
      _show_quote_first[0] = False
    elif opts.blank_line:
      print

    if opts.verbose:
      print "quote =", q
    text = q.text.strip()
    if opts.wrap:
      text = textwrap.fill(text, width=opts.width)

    attr = q.attribution or "(unknown)"
    if q.ref:
      attr += "; " + q.ref

    end_text = "-- %s [%s]" % (attr, collection)

    sep = " " if opts.oneline else "\n  "
    print sep.join((text, end_text))
    if opts.show_notes:
      for note in q.notes:
        print "#", note

  if opts.grep:
    if re.escape(opts.grep) == opts.grep:  # not a regex, could be improved
      opts.grep = opts.grep.lower()
      def grep(s):
        if not isinstance(s, basestring):
          return any(grep(x) for x in s)
        return opts.grep in s.lower()
    else:
      def grep(s):
        if not isinstance(s, basestring):
          return any(grep(x) for x in s)
        return re.compile(opts.grep, re.I).search(s)
    count = 0
    for collection, q in quotes:
      if any(grep(t) for t in q if t):
        show_quote(q, collection)
        count += 1
        if opts.n is not None and count == opts.n:
          break
  else:
    if opts.all:
      for collection, q in quotes:
        show_quote(q, collection)
    else:
      for _ in xrange(opts.n):
        collection, q = random.choice(quotes)
        show_quote(q, collection)
