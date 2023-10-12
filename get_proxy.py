import os
import requests

# os.environ['HTTP_PROXY'] = 'http://localhost:7890'
# os.environ['HTTPS_PROXY'] = 'http://localhost:7890'

# Clash REST API 地址
clash_api_url = 'http://localhost:9090/proxies'

# 发起 GET 请求获取代理列表
# secret = 'ac371ca9caa76fc5dbb00b168e03ef23c82d00396cab505368c22474280ccee9'
# response = requests.get(clash_api_url, headers={'Authorization': f'Bearer {secret}'})
response = requests.get(clash_api_url)

# 检查响应状态码
if response.status_code == 200:
    proxies = response.json()['proxies']
    print(proxies)

    # 打印代理列表
    for proxy in proxies:
        print(proxy)
else:
    print(response.status_code)
    print("无法获取代理列表")

# # 手动选择要使用的代理
# selected_proxy_index = input("请输入要使用的代理的索引: ")

# # 发起 PUT 请求设置 Clash 的代理
clash_config_url = 'http://localhost:9090/proxies/GLOBAL'
# requests.put(clash_config_url, json={'name': selected_proxy_index})
# print("已成功设置代理")

ips = set()
dict = {}
# 测试每个代理是否可用，以及其对应的ip
for proxy in proxies:
    requests.put(clash_config_url, json={'name': proxy})
    response = requests.get('http://api.ipify.org', proxies={'http': 'http://localhost:7890'})
    temp_ip = response.text
    print(temp_ip)
    ips.add(temp_ip)
    dict[proxy] = temp_ip

print(len(ips))

# save dict
import json
with open('proxy.json', 'w', encoding='utf-8-sig') as f:
    json.dump(dict, f, indent=4)