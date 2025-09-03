import json
import os
import requests
import logging
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning

cur_dir = os.path.abspath(os.path.dirname(__file__))
swr_log_file = os.path.join(cur_dir, 'swr_executor.log')
auth_json_file = os.path.join(cur_dir, 'auth.json')
images_json_file = os.path.join(cur_dir, 'images.json')

logging.basicConfig(filename=swr_log_file, filemode='a', level=logging.INFO, format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')

class SwrClient:
    def __init__(self, _swr_domain, _user_name, _password):
        self.swr_domain = _swr_domain
        self.user_name = _user_name
        self.password = _password
        self.api_auth = HTTPBasicAuth(_user_name, _password)

    def get_namespaces(self, params=None):
        url = 'https://%s/dockyard/v2/namespaces' % self.swr_domain
        logging.info('Start to get namespaces, url: %s' % url)
        res = requests.get(url, auth=self.api_auth, params=params, verify=False)
        if res.status_code != 200:
            logging.error('Unexpected error occurred, %s' % res.content)
            raise Exception('Unexpected error occurred, %s' % res.content)
        _namespaces = res.json()['namespaces']
        namespaces_ret = {}
        for _namespace in _namespaces:
            namespaces_ret[_namespace['name']] = 1
        return namespaces_ret

    def create_namespace(self, data):
        url = 'https://%s/dockyard/v2/namespaces' % self.swr_domain
        logging.info('Start to create namespaces, url: %s' % url)
        if isinstance(data, dict):
            data = json.dumps(data)
        res = requests.post(url, auth=self.api_auth, data=data, verify=False)
        if res.status_code != 201:
            logging.error('Unexpected error occurred, %s' % res.content)
            raise Exception('Unexpected error occurred, %s' % res.content)
        logging.info('Successfully created namespace.')

    def get_repositories(self, params=None):
        url = 'https://%s/dockyard/v2/repositories' % self.swr_domain
        logging.info('Start to get repositories, url: %s' % url)
        headers = {'Content-Type': 'application/json'}
        res = requests.get(url, auth=self.api_auth, headers=headers, params=params, verify=False)
        if res.status_code != 200:
            logging.error('Unexpected error occurred, %s' % res.content)
            raise Exception('Unexpected error occurred, %s' % res.content)
        repositories = res.json()
        logging.info('Got %s repositories' % len(repositories))
        return repositories

def read_json(_json_file) -> dict:
    logging.info('Start to read file: %s' % _json_file)
    with open(_json_file, 'r') as f:
        return json.load(f)

def write_json(_json_files, _json_content):
    with open(_json_files, 'w') as f:
        json.dump(_json_content, f, indent=4, ensure_ascii=False)


def get_auth_json():
    _auth_json = read_json(auth_json_file)
    if len(_auth_json.keys()) != 2:
        logging.error('Only support auth.json with two keys!')
        raise Exception('Only support auth.json with two keys!')
    _auth_json_with_property = {}
    for key, val in _auth_json.items():
        if not val.get('sync_property') or val.get('sync_property') not in ['from_region', 'to_region']:
            logging.error('sync_property must be defined and with correct value!')
            raise Exception('sync_property must be defined and with correct value!')
        sync_property = val.get('sync_property')
        if _auth_json_with_property.get(sync_property):
            logging.error('sync_property must be different!')
            raise Exception('sync_property must be different!')
        _auth_json_with_property[sync_property] = {'swr_domain': key, 'username': val['username'], 'password': val['password']}
    return _auth_json_with_property

def read_images_json():
    if not os.path.exists(images_json_file):
        with open(images_json_file, 'w') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
            return {}
    return read_json(images_json_file)



if __name__ == '__main__':
    auth_json = get_auth_json()

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    swr_from_client = SwrClient(auth_json['from_region']['swr_domain'], auth_json['from_region']['username'], auth_json['from_region']['password'])
    swr_to_client = SwrClient(auth_json['to_region']['swr_domain'], auth_json['to_region']['username'], auth_json['to_region']['password'])

    images_json = read_images_json()

    from_namespace = swr_from_client.get_namespaces()
    from_repo = swr_from_client.get_repositories({'limit': 65535})

    to_namespace = swr_to_client.get_namespaces()

    for namespace in from_namespace:
        if namespace not in to_namespace:
            logging.warning('namespace %s not exist in %s, well will try to create it!' % (namespace, auth_json['to_region']['swr_domain']))
            try:
                swr_to_client.create_namespace({'namespace': namespace})
            except Exception as e:
                logging.error('Create namespace %s failed, error message: %s' % (namespace, str(e)))

    need_refresh = False
    for repo in from_repo:
        repo_path = str(repo['path'])
        if repo_path not in images_json:
            repo_suffix = '/'.join(repo_path.split('/')[1:])
            images_json[repo_path] = '%s/%s' % (auth_json['to_region']['swr_domain'], repo_suffix)
            need_refresh = True
    if need_refresh:
        logging.info('Start to refresh json files.')
        write_json(images_json_file, images_json)


