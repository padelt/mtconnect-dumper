#!/usr/bin/env python3
import click, click_log
from datetime import datetime, timezone
from lxml import etree
import logging
import re
import requests
import os
import time

logger = logging.getLogger(__name__)

def validate_directory(cts, param, value):
    if not os.path.isdir(value):
        raise click.BadParameter("'%s' should be a directory!" % value)
    return value

class MTConnectSample():
    """Strip namespaces to make life a little easier."""
    re_split = re.compile(r"^(\{[^\}]+\}|[^:]+:)(.*)$")
    def __init__(self, source):
        parser = etree.XMLParser(ns_clean=True, recover=True) 
        self.root = etree.fromstring(source, parser=parser)
        self._dropns()
    
    def _dropns(self):
        """Go through tree and remove namespaces from tags."""
        for elem in self.root.iter():
            try:
                m = self.re_split.match(elem.tag)
            except:
                logger.error("Failed while dropping namespaces for element '%s' tag '%s' " % (repr(elem), repr(elem.tag)))
                raise
            if m:
                elem.tag = m.groups()[1]

@click.command()
@click.option('--url', default='http://localhost:5000', help="URL to MTConnect endpoint.")
@click.option('--prefix', default='mtconnect_', help="Start filenames with this.")
@click.option('--initial-count', default=1000000, help="Number of sequences to start requesting with.")
@click.argument('destination', callback=validate_directory)
@click_log.simple_verbosity_option()
@click_log.init(__name__)
def dump(url, prefix, initial_count, destination):
    while url.endswith('/'):
        url = url[:-1]
    seqno = 0
    count = initial_count
    connect_timeout_s = 5
    read_timeout_s = 60
    remove_filename = None
    while True:
        u = "%s/sample?from=%d&count=%d" % (url, seqno, count)
        logger.debug("About to request: %s" % u)
        filename = None
        got = None
        lowerbound = None
        maxcount = None
        try:
            req = requests.get(u, stream=True, timeout=(connect_timeout_s, read_timeout_s))
        except Exception as e:
            logger.exception("Connection to agent failed.")
        else:
            if req.status_code == 200:
                xml = req.raw.read()
                mts = MTConnectSample(xml)
                errors = mts.root.find('./Errors')
                if errors is not None:
                    oors = errors.findall("./Error[@errorCode='OUT_OF_RANGE']")
                    if len(oors) > 0:
                        # If the agent could not hold onto all data, it will error
                        # out if the requested 'from' value is below the first held
                        # sequence number. Get that minimum number and get that
                        # instead.
                        m = re.match("^.*from.*must be greater than or equal to (?P<lowerbound>\d+)\.$", oors[0].text)
                        if m:
                            lowerbound = int(m.groupdict()['lowerbound'])
                        # If the agent has a buffer smaller than what we requested
                        # in count, it will tell us to use this.
                        m = re.match("^.*count.*must be less than or equal to "
                                "(?P<maxcount>\d+)\.$", oors[0].text)
                        if m:
                            maxcount = int(m.groupdict()['maxcount'])
                    if lowerbound == None and maxcount == None:
                        logger.error('XML contained unknown error')
                        logger.error(repr(xml))

                if lowerbound != None:
                    logger.warn("Agent misses data down to sequence number %d. It advises to try %d." % (seqno, lowerbound))
                    seqno = lowerbound
                elif maxcount != None:
                    logger.warn("Agent informed us to request a maximum of "
                            "%d sequences at once instead of %d. Will do "
                            "in next request.", maxcount, count)
                    count = maxcount
                else:
                    # Get the next sequence number to request.
                    header = mts.root.find('./Header')
                    first_seq = int(header.get('firstSequence'))
                    last_seq = int(header.get('lastSequence'))
                    next_seq = int(header.get('nextSequence'))
                    got = next_seq-seqno
                    logger.debug("Sequence numbers agent holds: %d-%d, next is %d, "
                            "got %d starting from %d",
                            first_seq, last_seq, next_seq, next_seq-seqno, seqno)
                    # Write data to file.
                    date = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z').replace(':','.')
                    filename = os.path.join(destination, "%s%s_%19d-%d.xml" %
                            (prefix, date, seqno, got))
                    logger.debug("Writing to file: %s", filename)
                    with open(filename, 'wb') as f:
                        f.write(xml)

                    if remove_filename:
                        logger.debug("Removing empty last XML file: %s",
                                remove_filename)
                        os.unlink(remove_filename)
                        remove_filename = None

                    seqno = next_seq
            else:
                logger.error("Requesting '%s' failed with code %d" % (u,
                    req.status_code))

        if lowerbound == seqno or maxcount != None:
            # We have been advised that this is the lowest sequence number the
            # agent holds or to use lower count. Doing that immediately.
            logger.debug('Requesting immediately.')
        else:
            if got == 0:
                if filename:
                    # That file contains no sequences. We'll remove it once the
                    # next request is successful.
                    remove_filename = filename
                time.sleep(20)
            elif got == count:
                # There is more - go get it.
                time.sleep(1)
            else:
                time.sleep(60)

if __name__ == '__main__':
    dump()
