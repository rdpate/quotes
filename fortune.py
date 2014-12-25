import codecs
import glob
import locale
import optparse
import random
import re
import sys
import textwrap
from collections import namedtuple
from os import path
from pprint import pprint

import yaml


Quote = namedtuple("Quote", ["text", "attribution", "ref", "tags", "notes"])

def _main(args):
    if sys.stdout.encoding is None:
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout, errors="replace")

    optparser = optparse.OptionParser(usage="%prog [OPTION..] [QUOTE_FILE..]", add_help_option=False)
    optparser.add_option("-n", type="int", default=None,
        help="show N quotes")
    optparser.add_option("--grep", nargs=1, default=None,
        help="show quotes matching pattern")
    optparser.add_option("--notes", dest="show_notes", action="store_true", default=False,
        help="include notes")
    optparser.add_option("--width", type="int", default=79,
        help="wrap output lines, or 0 to disable [default %default]")
    optparser.add_option("--no-blank-line", dest="blank_line", action="store_false", default=True,
        help="don't output a blank line between each quote")
    optparser.add_option("--help", action="help",
        help="show this help and exit")
    optparser.add_option("--debug", action="store_true", default=False)
    opts, args = optparser.parse_args(args)

    if opts.n is None and opts.grep is None:
        opts.n = 1
    if opts.n is not None and opts.n < 1:
        optparser.error("invalid -n value")

    if not args:
        args = glob.glob(path.join(path.dirname(__file__), "quotes*.yaml"))

    if opts.debug:
        print "opts:", repr(opts)
        print "args:", repr(args)
        print "filenames:", repr(args)

    quotes = []
    for filename in args:
        if filename.startswith("-"):
            return "unexpected option"
        collection = path.basename(filename)
        for doc in yaml.load_all(codecs.open(filename, encoding="utf-8", errors="replace")):
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

    if opts.debug:
        print "[loaded {} quotes from {} files]".format(len(quotes), len(filenames))

    def show_quote(q, collection, is_first):
        if not is_first and opts.blank_line:
            print

        if opts.debug:
            print "quote =", q
        text = q.text.strip()
        if opts.width:
            text = textwrap.fill(text, width=opts.width)
        print text

        attr = q.attribution or "(unknown)"
        if q.ref:
            attr += "; " + q.ref

        end_text = u"  -- {}".format(attr)
        if opts.show_notes:
            end_text += u" [{}]".format(collection)
        print end_text

        if opts.show_notes:
            for note in q.notes:
                print "#", note

    if opts.grep:
        if re.escape(opts.grep) == opts.grep:  # test if a fixed-string match is possible, could be improved
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
                show_quote(q, collection, count == 0)
                count += 1
                if opts.n is not None and count == opts.n:
                    break
    else:
        for count in xrange(opts.n):
            collection, q = random.choice(quotes)
            show_quote(q, collection, count == 0)

def main(args):
    try:
        return _main(args)
    except KeyboardInterrupt:
        print
