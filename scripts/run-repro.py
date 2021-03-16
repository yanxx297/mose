#!/usr/bin/env python3.7

import os
import sys
import datetime
from datetime import timedelta
import shutil
import subprocess
import requests
from urllib.parse import urlparse
import bs4
from bs4 import BeautifulSoup
import argparse

kernel = "/home/yanxx297/Project/s2e/source/s2e-linux-kernel/linux"
workdir = "/home/yanxx297/Project/mose/workdir/syzbot" 

def get_repro(url, vid = None):
    repro = requests.get(url)
    rid = url.split("=")[2]
    path = rid
    if vid:
        path = os.path.join(vid, rid)
    path = os.path.join(workdir, path)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    f = open(os.path.join(path, "repro.c"), "wb")
    f.write(repro.content)
    f.close()
    return rid

def get_repros(ref):
    url = "https://syzkaller.appspot.com"
    response = requests.get(url+ref)
    vid = ref.split("=")[1]
    bs = BeautifulSoup(response.content, "html.parser")
    links = set()
    res = []

    for t in bs.find_all('a'):
        l = t.get('href', None)
        if l.startswith("/text?tag=ReproC&x="):
            links.add(l)

    print("C repro: " + str(len(links)))
    if len(links) == 0: 
        return res

    if not os.path.exists(vid): os.makedirs(vid)

    for l in links:
        res.append(get_repro(url + l, vid) )

    return res

def run_repros(ref, dryrun = False):
    list = get_repros(ref)
    for l in list:
        filepath = os.path.join(ref.split("=")[1],l)
        cmdline = ['gcc', '-no-pie', '-pthread', filepath + "/repro.c", '-g', '-o', filepath+"/repro"]
        proc = subprocess.Popen(cmdline)
        ret = proc.returncode
        if ret != 0:
            exit(1)

        if not dryrun:
            cmdline = ['bash', './run-s2e.sh', filepath]
            proc = subprocess.call(cmdline)


def _parse_table(content, target):
    bs = BeautifulSoup(content, "html.parser")
    tbs = bs.find_all('table', "list_table")
    res = []
    for tb in tbs:
        trs = tb.find_all('tr')
        for tr in trs[1:]:
            td = tr.find_all('td')
            if td[1].string == "C":
                now = datetime.datetime.now()
                timeReport = now
                if td[6].string:
                    timeReport -= timedelta(int(td[6].string.split('d')[0]))
                else:
                    timeReport -= timedelta(int(td[6].find_all('a')[0].string.split('d')[0]))
                timeLast = now - timedelta(int(td[5].string.split('d')[0]))
                if (timeLast <= target and timeReport >= target) or (timeReport <= target and timeLast >= target):
                    res.append(td[0].a.get('href', None))
                    print(td[0].string + "\t" + td[0].a.get('href', None).split("=")[1])
    return res

def get_cause_commit(url):
    response = requests.get(url)
    bs = BeautifulSoup(response.content, "html.parser")
    res = ""
    for b in bs.find_all('b'):
        if b.string and b.string.startswith('Cause bisection: the issue happens on the oldest tested release'):
            log = b.find_next_sibling('b')
            if log and log.a:
                log_url = '/'.join(url.split('/')[:3]) + log.a.get('href', None)
                res = requests.get(log_url).text.splitlines()[0].split(' ')[-1]
        elif b.string and b.string.startswith('Cause bisection'):
            s = b.find_next_sibling('span', class_='mono')
            if s.contents[0].split(' ')[0].endswith('commit'):
                res = s.contents[0].split(' ')[1]
            else:
                res = s.contents[0].split(' ')[0]
    return res.strip('\t\n')

def is_valid(kernel, fix, cause):
    def check_commit(commit):
        cmdline = ['git', '-C', kernel, 'merge-base', '--is-ancestor', commit, 'HEAD']
        proc = subprocess.Popen(cmdline, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.communicate()
        return proc.returncode
    return (check_commit(fix) != 0 and check_commit(cause) == 0)

def parse_table(_url, content):
    bs = BeautifulSoup(content, "html.parser")
    tbs = bs.find_all('table', "list_table")
    res = []
    for tb in tbs:
        trs = tb.find_all('tr')
        for tr in trs[1:]:
            td = tr.find_all('td')
            if td[1].string == "C" and td[2].string == "done":
                fix = td[8].a.get('href', None).split('=')[1]
                url = '/'.join(_url.split('/')[:3]) + td[0].a.get('href', None)
                cause = get_cause_commit(url)
                if is_valid(kernel, fix, cause):
                    print (td[0].string + " fix " + fix + ", cause " + cause)
                    res.append(url)
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("url", nargs='*')
    args = parser.parse_args()
    url = "https://syzkaller.appspot.com/upstream/fixed" 

    if args.url:
        rid = get_repro(args.url[0]) 
    else:
        fd = open("fixed.html", "r")
        list = parse_table(url, fd.read())
#        target = datetime.datetime(2019, 1, 13)
#        list = parse_table(fd.read(), target)
#        for l in list:
#            run_repros(l, args.dry_run)
