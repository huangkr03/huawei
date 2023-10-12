import requests
# import grequests
from bs4 import BeautifulSoup


def find_info(url, file_name='', pom_name=None):
    if url == '':
        return file_name, '', '', '', '', '', ''
    if url[-1] != '/':
        url += '/'
    # run session
    session = requests.Session()
    try:
        response = session.get(url)
    except Exception:
        session.close()
        return file_name, '', '', '', '', '', ''
    if response.status_code != 200:
        session.close()
        return file_name, '', '', '', '', '', ''
    soup = BeautifulSoup(response.text, 'html.parser')
    a = soup.find_all('a')
    files = {i.get('title') if i.get('title') else i.text: i.get('href') for i in a}

    source_md5 = ''
    source_sha1 = ''
    jar_md5 = ''
    jar_sha1 = ''
    pom_md5 = ''
    pom_sha1 = ''

    if file_name:
        jar = file_name
    else:
        jars = [i for i in files.keys() if i.endswith('.jar')]
        # find the shortest jar file
        jar = min(jars, key=lambda x: len(x)) if len(jars) > 0 else None
    if not jar:
        aars = [i for i in files.keys() if i.endswith('.aar')]
        jar = min(aars, key=lambda x: len(x)) if len(aars) > 0 else None
    if not jar:
        wars = [i for i in files.keys() if i.endswith('.war')]
        jar = min(wars, key=lambda x: len(x)) if len(wars) > 0 else None
    if pom_name:
        pom = pom_name
    else:
        poms = [i for i in files.keys() if i.endswith('.pom')]
        pom = min(poms, key=lambda x: len(x)) if len(poms) > 0 else None
    source_jars = [i for i in files.keys() if i.endswith('-sources.jar')]
    source_jar = min(source_jars, key=lambda x: len(x)) if len(source_jars) > 0 else None
    try:
        if source_jar:
            source_md5 = files.get(source_jar + '.md5') or ''
            source_sha1 = files.get(source_jar + '.sha1') or ''
            if source_md5:
                temp_response = session.get(url + source_md5)
                if temp_response.status_code == 200:
                    source_md5 = temp_response.text.strip()[:32]
                else:
                    source_md5 = ''
            if source_sha1:
                temp_response = session.get(url + source_sha1)
                if temp_response.status_code == 200:
                    source_sha1 = temp_response.text.strip()[:40]
                else:
                    source_sha1 = ''
        if jar:
            jar_md5 = files.get(jar + '.md5') or ''
            jar_sha1 = files.get(jar + '.sha1') or ''
            if jar_md5:
                temp_response = session.get(url + jar_md5)
                if temp_response.status_code == 200:
                    jar_md5 = temp_response.text.strip()[:32]
                else:
                    jar_md5 = ''
            if jar_sha1:
                temp_response = session.get(url + jar_sha1)
                if temp_response.status_code == 200:
                    jar_sha1 = temp_response.text.strip()[:40]
                else:
                    jar_sha1 = ''
        if pom:
            pom_md5 = files.get(pom + '.md5') or ''
            pom_sha1 = files.get(pom + '.sha1') or ''
            if pom_md5:
                temp_response = session.get(url + pom_md5)
                if temp_response.status_code == 200:
                    pom_md5 = temp_response.text.strip()[:32]
                else:
                    pom_md5 = ''
            if pom_sha1:
                temp_response = session.get(url + pom_sha1)
                if temp_response.status_code == 200:
                    pom_sha1 = temp_response.text.strip()[:40]
                else:
                    pom_sha1 = ''
    except Exception:
        pass

    session.close()
    return jar, source_md5, source_sha1, jar_md5, jar_sha1, pom_md5, pom_sha1


def find_link(url, filename='', maven_jar_link='', maven_pom_link = ''):
    if url == '':
        return filename, maven_jar_link, maven_pom_link
    if url[-1] != '/':
        url += '/'
    # run session
    try:
        response = requests.get(url)
    except Exception:
        return filename, maven_jar_link, maven_pom_link
    if response.status_code != 200:
        return filename, maven_jar_link, maven_pom_link
    soup = BeautifulSoup(response.text, 'html.parser')
    a = soup.find_all('a')
    files = {i.get('title') if i.get('title') else i.text: i.get('href') for i in a}

    if not maven_jar_link:
        jars = [i for i in files.keys() if i.endswith('.jar')]
        # find the shortest jar file
        maven_jar_link = min(jars, key=lambda x: len(x)) if len(jars) > 0 else ''
    if not maven_jar_link:
        aars = [i for i in files.keys() if i.endswith('.aar')]
        maven_jar_link = min(aars, key=lambda x: len(x)) if len(aars) > 0 else ''
    if not maven_jar_link:
        wars = [i for i in files.keys() if i.endswith('.war')]
        maven_jar_link = min(wars, key=lambda x: len(x)) if len(wars) > 0 else ''
    if not maven_pom_link:
        poms = [i for i in files.keys() if i.endswith('.pom')]
        maven_pom_link = min(poms, key=lambda x: len(x)) if len(poms) > 0 else ''
    
    if maven_jar_link and not maven_jar_link.startswith('http'):
        maven_jar_link = url + maven_jar_link.strip('/')
    if maven_pom_link and not maven_pom_link.startswith('http'):
        maven_pom_link = url + maven_pom_link.strip('/')
    
    return filename, maven_jar_link, maven_pom_link


if __name__ == '__main__':
    print(find_info('https://repo1.maven.org/maven2/log4j/log4j/1.2.17'))

    print()
