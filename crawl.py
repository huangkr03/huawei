import time
import traceback
import atexit
import csv
import json
import os
import sys
from datetime import datetime

from curl_cffi import requests
from bs4 import BeautifulSoup

from FindInfo import find_info, find_link

append_data = []
interval = 3
current_length = 0
max_length = 100000
start_time = time.time()
imp = 'edge99'

# 设置环境变量(使用clash的HTTP代理)
# if --proxy or -p
if len(sys.argv) > 1:
    if sys.argv[1] == '--proxy' or sys.argv[1] == '-p':
        os.environ['HTTP_PROXY'] = 'http://localhost:7890'
        os.environ['HTTPS_PROXY'] = 'http://localhost:7890'

base_url = 'https://mvnrepository.com/artifact/'
files = os.listdir('datas')
files.sort()
current_length += max((len(files) - 1) * max_length, 0)
latest_data = files[-1]

with open('datas/' + latest_data, encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    row = None
    while True:
        try:
            row = next(reader)
            current_length += 1
        except StopIteration:
            break
    if row:
        last_group_id = row[2]
        last_artifact_id = row[3]
        last_version = row[4]
    else:
        last_group_id = ''
        last_artifact_id = ''
        last_version = ''


def save_data():
    with open(f'datas/{latest_data}', 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerows(append_data)
    append_data.clear()


def get_latest_data_filename():
    files = os.listdir('datas')
    files.sort()
    latest_data = files[-1]
    return latest_data

def new_data_file():
    global current_length
    global latest_data
    latest_data = f'data{len(os.listdir("datas"))}.csv'
    with open(f'datas/{latest_data}', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

atexit.register(save_data)


def date_trans(datestr):
    # 将输入日期字符串解析为datetime对象
    date_obj = datetime.strptime(datestr, "%b %d, %Y")

    # 格式化日期为所需的字符串格式
    output_date = date_obj.strftime("%Y-%#m-%#d")
    return output_date


def get_body(soup):
    tbody = soup.find('table')
    # for every tr in tbody, get {th: td}
    trs = tbody.select('tr')
    body = {}
    for tr in trs:
        th = tr.select_one('th').text.strip()
        td = tr.select_one('td')
        body[th] = td
    return body


def get_version_sections(soup):
    sections = soup.select('.version-section')
    version_sections = {section.select_one('h1, h2, h3, h4, h5, h6').text.strip(): section for section in sections}
    return version_sections


def ip_test():
    response = requests.get('https://mvnrepository.com/artifact/com.github.albfernandez.seam/jboss-seam-excel/2.3.27.ayg', impersonate=imp)
    if response.status_code == 403:
        print('IP被封禁了，403')
        sys.exit(1)
    if 'Just a moment...' in response.text:
        print('IP被封禁了')
        sys.exit(1)
    elif "gtag('js', new Date());" not in response.text:
        print('CDN异常')
        print(response.status_code)
        sys.exit(1)
    else:
        return True


# Helper function to extract information from the Maven page
def extract_info(response):
    if "gtag('js', new Date());" not in response.text:
        print('CDN异常')
        print(response.status_code)
        sys.exit(1)
    comp_name = ''
    description = ''
    categories = ''
    used_cnt = ''

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        comp_name = soup.select_one('.im-title').text.strip()
        description = soup.select_one('.im-description').text.replace('\n', ' ').strip()

        body = get_body(soup)

        categories_ = body.get('Categories')
        categories = categories_.text.strip() if categories_ else ''

        used_cnt_ = body.get('Used By')
        used_cnt = used_cnt_.text.rstrip('artifacts').strip() if used_cnt_ else ''
    except Exception as e:
        print(f'\n{url}')
        traceback.print_exc()

    return comp_name, description, categories, used_cnt


# Helper function to extract version information from the Maven page
def extract_version_info(url, session=None):
    release_date = ''
    file_name = ''
    homepage = ''
    maven_url = ''
    vulnerabilities = {'directVulns': [], 'indirectVulns': []}
    compile_dependencies = []
    provided_dependencies = []
    test_dependencies = []
    runtime_dependencies = []
    maven_jar_link = ''
    maven_pom_link = ''
    tags = ''
    developers = []
    comp_organization = ''
    comp_organization_url = ''
    license = ''
    license_url = ''
    try:
        if session:
            response = session.get(url)
        else:
            response = requests.get(url, impersonate=imp)
        
        if "gtag('js', new Date());" not in response.text:
            print('CDN异常')
            print(response.status_code)
            sys.exit(1)
        if response.status_code != 200:
            if response.status_code == 403:
                ip_test()
            print(f'\nStatus Code: {response.status_code}\t{url}')
            return release_date, file_name, homepage, \
                   maven_url, vulnerabilities, developers, comp_organization, comp_organization_url, license, license_url, \
                   compile_dependencies, provided_dependencies, test_dependencies, maven_jar_link, maven_pom_link, \
                   runtime_dependencies, tags
        soup = BeautifulSoup(response.content, 'html.parser')
        body = get_body(soup)

        release_date_ = body.get('Date')
        release_date = date_trans(release_date_.text.strip()) if release_date_ else ''

        files = body.get('Files')
        files = files.select('a') if files else []
        urls = {file.text.strip(): file['href'] for file in files}
        for url_ in urls:
            if not maven_jar_link:
                if 'jar' in url_:
                    maven_jar_link = urls[url_]
                    file_name = maven_jar_link.split('/')[-1]
                elif 'bundle' in url_:
                    maven_jar_link = urls[url_]
                    file_name = maven_jar_link.split('/')[-1]
                elif 'aar' in url_:
                    maven_jar_link = urls[url_]
                    file_name = maven_jar_link.split('/')[-1]
            if not maven_pom_link and 'pom' in url_:
                maven_pom_link = urls[url_]
        
        if not maven_jar_link or not maven_pom_link:
            for url_ in urls:
                if not maven_jar_link and urls[url_].endswith('.jar'):
                    maven_jar_link = urls[url_]
                    file_name = maven_jar_link.split('/')[-1]
                if not maven_pom_link and urls[url_].endswith('.pom'):
                    maven_pom_link = urls[url_]
                
        if not maven_jar_link:
            for url_ in urls:
                if urls[url_].endswith('.aar') or urls[url_].endswith('.war'):
                    maven_jar_link = urls[url_]
                    file_name = maven_jar_link.split('/')[-1]
                    break

        view_all = urls.get('View All')
        maven_url = view_all if view_all else ''
        maven_url = maven_url.rstrip('/') + '/' if maven_url else ''

        if not maven_jar_link or not maven_pom_link:
            file_name, maven_jar_link, maven_pom_link = find_link(maven_url, filename=file_name, maven_jar_link=maven_jar_link, maven_pom_link=maven_pom_link)

        homepage_ = body.get('HomePage')
        homepage_a = homepage_.select_one('a') if homepage_ else None
        homepage = homepage_a['href'] if homepage_a else ''

        tags_ = body.get('Tags')
        tags_a = tags_.select('a') if tags_ else []
        tags = ' '.join([tag.text.strip() for tag in tags_a] if tags_a else [])

        version_sections = get_version_sections(soup)
        for section in version_sections:
            if 'Compile Dependencies' in section:
                trs = version_sections[section].find('tbody').select('tr')
                for tr in trs:
                    tds = tr.select('td')
                    td = tds[2]
                    group_artifact = td.text.strip()
                    if group_artifact.endswith('vulnerability'):
                        group_artifact = group_artifact.rstrip('1 vulnerability')
                    elif group_artifact.endswith('vulnerabilities'):
                        # find a with class vuln
                        try:
                            vul = td.select_one('a.vuln')
                            text = vul.text.strip()
                            group_artifact = group_artifact.replace(text, '')
                        except Exception:
                            pass
                    temp_group_id, temp_artifact_id = group_artifact.replace('\n', '').replace(' ', '').split('»')
                    version = tds[3].text.strip()
                    try:
                        version_a = tds[3].find('a')
                        version = version_a['href'].split('/')[-1] if version_a else version
                    except Exception:
                        pass
                    compile_dependencies.append(
                        {'groupId': temp_group_id, 'artifactId': temp_artifact_id, 'version': version})
            elif 'Provided Dependencies' in section:
                trs = version_sections[section].find('tbody').select('tr')
                for tr in trs:
                    tds = tr.select('td')
                    td = tds[2]
                    group_artifact = td.text.strip()
                    if group_artifact.endswith('vulnerability'):
                        group_artifact = group_artifact.rstrip('1 vulnerability')
                    elif group_artifact.endswith('vulnerabilities'):
                        # find a with class vuln
                        try:
                            vul = td.select_one('a.vuln')
                            text = vul.text.strip()
                            group_artifact = group_artifact.replace(text, '')
                        except Exception:
                            pass
                    temp_group_id, temp_artifact_id = group_artifact.replace('\n', '').replace(' ', '').split('»')
                    version = tds[3].text.strip()
                    try:
                        version_a = tds[3].find('a')
                        version = version_a['href'].split('/')[-1] if version_a else version
                    except Exception:
                        pass
                    provided_dependencies.append(
                        {'groupId': temp_group_id, 'artifactId': temp_artifact_id, 'version': version})
            elif 'Test Dependencies' in section:
                trs = version_sections[section].find('tbody').select('tr')
                for tr in trs:
                    tds = tr.select('td')
                    td = tds[2]
                    group_artifact = td.text.strip()
                    if group_artifact.endswith('vulnerability'):
                        group_artifact = group_artifact.rstrip('1 vulnerability')
                    elif group_artifact.endswith('vulnerabilities'):
                        # find a with class vuln
                        try:
                            vul = td.select_one('a.vuln')
                            text = vul.text.strip()
                            group_artifact = group_artifact.replace(text, '')
                        except Exception:
                            pass
                    temp_group_id, temp_artifact_id = group_artifact.replace('\n', '').replace(' ', '').split('»')
                    version = tds[3].text.strip()
                    try:
                        version_a = tds[3].find('a')
                        version = version_a['href'].split('/')[-1] if version_a else version
                    except Exception:
                        pass
                    test_dependencies.append(
                        {'groupId': temp_group_id, 'artifactId': temp_artifact_id, 'version': version})
            elif 'Runtime Dependencies' in section:
                trs = version_sections[section].find('tbody').select('tr')
                for tr in trs:
                    tds = tr.select('td')
                    td = tds[2]
                    group_artifact = td.text.strip()
                    if group_artifact.endswith('vulnerability'):
                        group_artifact = group_artifact.rstrip('1 vulnerability')
                    elif group_artifact.endswith('vulnerabilities'):
                        # find a with class vuln
                        try:
                            vul = td.select_one('a.vuln')
                            text = vul.text.strip()
                            group_artifact = group_artifact.replace(text, '')
                        except Exception:
                            pass
                    temp_group_id, temp_artifact_id = group_artifact.replace('\n', '').replace(' ', '').split('»')
                    version = tds[3].text.strip()
                    try:
                        version_a = tds[3].find('a')
                        version = version_a['href'].split('/')[-1] if version_a else version
                    except Exception:
                        pass
                    runtime_dependencies.append(
                        {'groupId': temp_group_id, 'artifactId': temp_artifact_id, 'version': version})
            elif 'Licenses' in section:
                trs = version_sections[section].find('tbody').select('tr')
                licenses = []
                license_urls = []
                for tr in trs:
                    tds = tr.select('td')
                    license = tds[0].text.strip()
                    try:
                        license_a = tds[1].select_one('a')
                        license_url = license_a['href']
                    except Exception:
                        license_url = tds[1].text.strip()
                    licenses.append(tds[0].text.strip())
                    license_urls.append(license_url)
                if len(licenses) > 0:
                    license = ', '.join(licenses)
                    license_url = ', '.join(license_urls)
            elif 'Developers' in section:
                ths = version_sections[section].find('thead').find('tr').select('th')
                trs = version_sections[section].find('tbody').select('tr')
                for tr in trs:
                    tds = tr.select('td')
                    developers.append({th.text.strip(): td.text.strip() for th, td in zip(ths, tds)})

        vulnerabilities_ = body.get('Vulnerabilities')
        if vulnerabilities_:
            spans = vulnerabilities_.select('span')
            current_vulns = []
            for span in spans:
                # if span has class vulnmsg
                if 'vulnmsg' in span['class']:
                    if 'Direct' in span.text:
                        current_vulns = vulnerabilities['directVulns']
                    else:
                        current_vulns = vulnerabilities['indirectVulns']
                else:
                    current_vulns.append(span.text.strip())

        comp_organization_ = body.get('Organization')
        comp_organization = comp_organization_.text.strip() if comp_organization_ else ''
        comp_organization_url_ = comp_organization_.select_one('a') if comp_organization_ else None
        comp_organization_url = comp_organization_url_['href'] if comp_organization_url_ else ''

    except Exception as e:
        print(f'\n{url}')
        traceback.print_exc()

    return release_date, file_name, homepage, maven_url, \
           vulnerabilities, developers, comp_organization, comp_organization_url, license, license_url, \
           compile_dependencies, provided_dependencies, test_dependencies, maven_jar_link, maven_pom_link, \
           runtime_dependencies, tags


# Main code
if __name__ == '__main__':
    current_time = time.time()
    if ip_test():
        print('网页获取正常')
    try:
        with open('gav.json') as f:
            gavs = json.load(f)

        if last_group_id:
            skip_group = True
            skip_artifact = True
            skip_version = True
        else:
            skip_group = False
            skip_artifact = False
            skip_version = False

        current_group = 0
        current_artifact = 0
        current_version = 0
        for group_id in gavs:
            current_group += 1
            if skip_group and group_id != last_group_id:
                continue
            skip_group = False
            group = gavs[group_id]
            for artifact_id in group:
                current_time = time.time()
                current_artifact += 1
                if skip_artifact and artifact_id != last_artifact_id:
                    continue
                skip_artifact = False
                url = f'{base_url}{group_id}/{artifact_id}'

                try:
                    for i in range(5):
                        session = requests.Session(impersonate=imp)
                        response = session.get(url)
                        if response.status_code == 200:
                            comp_name, description, categories, used_cnt = extract_info(response)
                            break
                        elif response.status_code == 403:
                            session.close()
                            ip_test()
                    else:
                        session = requests.Session(impersonate=imp)
                except Exception as e:
                    print(f'\n{url}')
                    traceback.print_exc()
                    comp_name, description, categories, used_cnt = '', '', '', ''
                    session.close()
                    session = requests.Session(impersonate=imp)

                artifact = group[artifact_id]
                for version in artifact:
                    current_version += 1
                    maven_id = f'{group_id}{artifact_id}{version}'
                    if skip_version:
                        if version != last_version:
                            continue
                        else:
                            skip_version = False
                            continue
                    print(
                        f'\rcurrent: {current_length + 1} {current_group}/{len(gavs)}\t{current_artifact}/{len(group)} '
                        f'{current_version}/{len(artifact)}\t{group_id}:{artifact_id}:{version}', end='')
                    url = f'{base_url}{group_id}/{artifact_id}/{version}'
                    temp_time = time.time()
                    if temp_time - current_time < interval:
                        time.sleep(interval - (temp_time - current_time))
                        current_time = time.time()
                    release_date, file_name, homepage, \
                    maven_url, vulnerabilities, developers, comp_organization, comp_organization_url, license, license_url, \
                    compile_dependencies, provided_dependencies, test_dependenciesm, maven_jar_link, maven_pom_link, \
                    runtime_dependencies, tags = extract_version_info(url, session)

                    row = [maven_id, comp_name, group_id, artifact_id, version, file_name, release_date, description,
                           categories, homepage, maven_url,
                           used_cnt, vulnerabilities, developers, comp_organization,
                           comp_organization_url, license, license_url, compile_dependencies, provided_dependencies,
                           test_dependenciesm, maven_jar_link, maven_pom_link, runtime_dependencies, tags]
                    if current_length % max_length == 0:
                        save_data()
                        new_data_file()
                    if current_length % 1001 == 0:
                        if time.time() - current_time < interval:
                            time.sleep(interval - (time.time() - current_time))
                        current_time = time.time()
                    current_length += 1
                    append_data.append(row)
                    # save_data()
                session.close()
                current_version = 0
            save_data()
            current_artifact = 0
    except KeyboardInterrupt:
        print()
        print('Data saved.')
        pass
