import configparser
import requests
import json
import base64
import hashlib
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os


class MaapAuthenticator(object):

    def __init__(self,auth_config_path,maap_config_path) -> None:

        config = configparser.ConfigParser()
        config.read(auth_config_path)

        #Retrieve auth values
        self.login = config['auth']['email']
        self.password = config['auth']['password']

        config = configparser.ConfigParser()
        config.read(maap_config_path)

        #Retrieve maap values
        self.client_id = config['maap']['client_id']
        self.url_token = config['maap']['url_token']


    
    def get_esa_token_with_esa_cred(self) -> str:

        response = requests.post(self.url_token, data={'client_id': self.client_id, 'username': self.login, 'password': self.password,
                                                        "grant_type": "password", "scope": "profile"})
        data = json.loads(response.text)
        return data['access_token']
    

    def get_esa_token_with_nasa_cred(self) -> str:
        
        session = requests.Session()

        response = session.get("https://auth.val.esa-maap.org/realms/maap/.well-known/openid-configuration")
        openid_config = json.loads(response.text)

        response = session.get(openid_config["jwks_uri"])
        certs = json.loads(response.text)



        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
        code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)

        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.replace('=', '')

        response = session.get(openid_config["authorization_endpoint"],
                                params={"redirect_uri":"https://portal.val.esa-maap.org/portal-val/ESA/home",
                                        "response_type":"code",
                                        "client_id":"portal",
                                        "scope":"openid profile offline_access email",
                                        "code_challenge_method":"S256",
                                        "code_challenge":code_challenge})

        soup = BeautifulSoup(response.text, 'html.parser')
        nasa_broker_url = ""
        for link in soup.find_all('a'):
            if 'broker/NASA/' in link.get('href'):
                nasa_broker_url = link.get('href')

        # Click on NASA in keycloak
        response = session.get("https://auth.val.esa-maap.org"+nasa_broker_url)

        soup = BeautifulSoup(response.text, 'html.parser')

        redirect_url = ""
        for link in soup.find_all('a'):
            if'EarthData' in link.text:
                redirect_url = link.get("href")


        # Click on Earth data in CAS
        response = session.get("https://auth.maap-project.org/cas/"+redirect_url)

        soup = BeautifulSoup(response.text, 'html.parser')

        authenticity_token=""
        client_id=""
        redirect_uri=""

        for tag in soup.find_all("input", type="hidden"):
            if tag.get("name") == "authenticity_token":
                authenticity_token = tag.get("value")
            if tag.get("name") == "client_id":
                client_id = tag.get("value")
            if tag.get("name") == "redirect_uri":
                redirect_uri = tag.get("value")
    
        

        data_urs = {
            "authenticity_token": authenticity_token,
            "username":self.login,
            "password": self.password,
            "client_id": client_id,
            "redirect_uri":redirect_uri,
            "response_type":"code",
            }

        # Click on login in URS
        response = session.post("https://urs.earthdata.nasa.gov/login",data = data_urs)


        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup.find_all("a", id="redir_link"):
            redirect_url = tag.get("href")

        # Follow redirection
        response = session.get(redirect_url)

        parsed_url  = urlparse(response.history[-1].headers['Location'])
        code = parse_qs(parsed_url.query)['code'][0]



        response = session.post("https://auth.val.esa-maap.org/realms/maap/protocol/openid-connect/token",
                                data={
                                    "grant_type":"authorization_code",
                                    "code":code,
                                    "client_id":"portal",
                                    "code_verifier":code_verifier,
                                    "redirect_uri":"https://portal.val.esa-maap.org/portal-val/ESA/home"
                                
        })

        return json.loads(response.text)['access_token']
