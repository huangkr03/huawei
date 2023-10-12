from pprint import pprint
import random
import time
from curl_cffi import requests
import json

def pool_test():
    ips = set()
    with open('/home/huang/python_project/huawei/proxy.json', 'r', encoding='utf-8-sig') as f:
        proxies = json.load(f)
    for i in proxies:
        ips.add(proxies[i])
    if '' in ips:
        ips.remove('')
    ip_pool = {ip: [] for ip in ips}
    for i in proxies:
        if proxies[i] != '':
            ip_pool[proxies[i]].append(i)

    safe_ip_pool = {}

    for ip in ips:
        # test ip
        for proxy in ip_pool[ip]:
            print(f"当前测试proxy: {proxy}")
            rp = requests.put('http://localhost:9090/proxies/GLOBAL', json={'name': proxy})
            temp_trial = 0
            while rp.status_code != 204:
                print(f"设置代理{proxy}失败，状态码：{rp.status_code}")
                rp = requests.put('http://localhost:9090/proxies/GLOBAL', json={'name': proxy})
                temp_trial += 1
                if temp_trial == 5:
                    temp_trial = -1
                    break
            if temp_trial == -1:
                print(f"设置代理{proxy}失败，跳过")
                continue
            time.sleep(random.randint(5, 8))
            temp = 0
            while True:
                try:
                    response = requests.get('https://mvnrepository.com/', proxies={'https': 'http://localhost:7890'}, impersonate='chrome110')
                    if response.status_code == 200 and 'gtag(' not in response.text:
                        print(f'{ip} is not safe')
                    elif response.status_code != 200:
                        print(f'{ip} {response.status_code}')
                    else:
                        if safe_ip_pool.get(ip) is None:
                            safe_ip_pool[ip] = []
                        safe_ip_pool[ip].append(proxy)
                        print(f'{ip} is safe')
                    break
                except Exception as e:
                    print(e)
                    print('遇到错误，等待5秒后重试')
                    temp += 1
                    if temp == 5:
                        break
                    time.sleep(5)
                    
    # save ip_pool
    with open('safe_ip_pool.json', 'w', encoding='utf-8-sig') as f:
        json.dump(safe_ip_pool, f, indent=4)

if __name__ == '__main__':
    pool_test()