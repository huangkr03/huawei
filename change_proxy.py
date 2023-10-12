import json
from pprint import pprint
import random
import sys
import time

from curl_cffi import requests


current = 0
total_interval = 15
clash_config_url = 'http://localhost:9090/proxies/GLOBAL'


# ips = set()
with open('/home/huang/python_project/huawei/proxy.json', 'r', encoding='utf-8-sig') as f:
    proxies = json.load(f)
# for i in proxies:
#     ips.add(proxies[i])
# ips.remove('')
# ip_pool = {ip: [] for ip in ips}
# for i in proxies:
#     if proxies[i] != '':
#         ip_pool[proxies[i]].append(i)
with open('safe_ip_pool.json', 'r', encoding='utf-8-sig') as f:
    ip_pool = json.load(f)
ips = set(ip_pool.keys())
total = len(ips)
current_proxy = ''

def init_proxy():
    global current, current_proxy
    current = random.randint(0, total - 1)
    current_proxy = random.choice(ip_pool[list(ips)[current]])
    requests.put(clash_config_url, json={'name': current_proxy})
    print(f'已成功设置代理：{current_proxy}')

def remove_proxy(proxy):
    global total
    ip = proxies[proxy]
    ip_pool[ip].remove(proxy)
    if len(ip_pool[ip]) == 0:
        ip_pool.pop(ip)
        ips.remove(ip)
        total = len(ips)
    else:
        print(f'ip {str(ip)} {len(ip_pool[ip])}个节点已被封禁，剩余的代理节点：{str(ip_pool[ip])}')

def change_proxy():
    global current, current_proxy
    # if total <= 1:
    #     print('ip数量不足，无法切换')
    #     send_message('ip数量不足', f"剩余ip数量：{str(total)}")
    #     sys.exit(0)
    if total == 0:
        return None
    current = (current + 1) % total
    temp_proxy = random.choice(ip_pool[list(ips)[current]])
    rp = requests.put(clash_config_url, json={'name': temp_proxy})
    temp_trial = 0
    while rp.status_code != 204:
        print(f"设置代理{temp_proxy}失败，状态码：{rp.status_code}")
        rp = requests.put(clash_config_url, json={'name': temp_proxy})
        temp_trial += 1
        if temp_trial == 5:
            remove_proxy(temp_proxy)
    print(f'已成功设置代理：{temp_proxy}')
    current_proxy = temp_proxy

def remove_ip():
    global total
    ip = proxies[current_proxy]
    safe_proxies = []
    # test all proxies in ip
    for proxy in ip_pool[ip]:
        print(f"当前测试proxy: {proxy}")
        rp = requests.put(clash_config_url, json={'name': proxy})
        temp_trial = 0
        while rp.status_code != 204:
            print(f"设置代理{proxy}失败，状态码：{rp.status_code}")
            rp = requests.put(clash_config_url, json={'name': proxy})
            temp_trial += 1
            if temp_trial == 5:
                remove_proxy(proxy)
        time.sleep(random.randint(5, 8))
        temp = 0
        while True:
            try:
                response = requests.get('https://mvnrepository.com/', proxies={'https': 'http://localhost:7890'}, impersonate='chrome110')
                if response.status_code == 200 and "gtag('js', new Date());" not in response.text:
                    print(f'{ip} is not safe')
                elif response.status_code != 200:
                    print(f'{ip} {response.status_code}')
                else:
                    print(f'{ip} is safe')
                    safe_proxies.append(proxy)
                break
            except Exception as e:
                print(e)
                print('遇到错误，等待5秒后重试')
                temp += 1
                if temp == 5:
                    break
                time.sleep(5)
    if len(safe_proxies) == 0:
        ip_pool.pop(ip)
        ips.remove(ip)
        total = len(ips)
    else:
        print(f'ip {str(ip)} {len(ip_pool[ip]) - len(safe_proxies)}个节点已被封禁，剩余的代理节点：{str(safe_proxies)}')
        ip_pool[ip] = safe_proxies
    change_proxy()


def get_current_proxy():
    return current_proxy

def get_ip_num():
    return total

def get_interval(interval=None):
    if interval:
        return interval
    # save .2
    interval = round(total_interval / total, 2)
    print(f'interval: {interval}')
    return interval

