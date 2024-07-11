import requests
import json
import time
from typing import List
import configparser
import os

class MaapProcess(object):

    def __init__(self, id: str, title: str) -> None: 
        self.id = id
        self.title = title

class MaapJob(object):

    def __init__(self,p_id:str, job_id:str, dps_name:str) -> None:
        self.p_id = p_id
        self.job_id = job_id
        self.status = "NONE"
        self.dps_name = dps_name

class MaapWPST(object):

    def __init__(self,maap_ini_path: str,oauth_token: str) -> None:

        config = configparser.ConfigParser()
        config.read(maap_ini_path)
        self.copa_backend_url = config['maap']['copa_backend_url']
        self.oauth_token = oauth_token
        self.process_list = self.__load_process()

    def __load_process(self) -> List[MaapProcess]:

        response = requests.get(self.copa_backend_url+'wpst/processes',headers = {'Authorization': 'Bearer '+ self.oauth_token})
        response.raise_for_status()

        results = []
        for process_json in response.json()['processes']:
            results.append(MaapProcess(process_json['id'],process_json['title']))

        return results
    
    
    def job_status(self,maap_job: MaapJob) -> str:

        response = requests.get(self.copa_backend_url+'wpst/processes/'+maap_job.p_id+'/jobs/'+maap_job.job_id,headers = {'Authorization': 'Bearer '+ self.oauth_token})
        response.raise_for_status()

        res_json = response.json()
        if 'status' in res_json:
            result = res_json['status']

        return result


    def launch_process(self,title,inputs) -> MaapJob:

        p_id = None
        for process in self.process_list:
            if title == process.title:
                p_id = process.id
        job_id = None

        if p_id is not None:                             
            payload = {'inputs':inputs,'outputs':[],'mode':'ASYNC','response':'RAW'}
            response = requests.post(self.copa_backend_url+'wpst/processes/'+p_id+'/jobs',json=payload,headers = {'Authorization': 'Bearer '+ self.oauth_token})
            response.raise_for_status()
            res_json = response.json()

            if 'jobId' in res_json:
                print(response.json())
                job_id = response.json()['jobId']
                dps_name  = response.json()['message'].split('/')[-1]
        else:
            print("ERROR : Can not launch job for process :"+title+" !")

        return MaapJob(p_id,job_id,dps_name)
    
    def wait_for_final_status(self, maap_job):        
        job_status = 'RUNNING'

        while job_status not in ['SUCCEEDED','FAILED']:

            response = requests.get(self.copa_backend_url+'wpst/processes/{}/jobs/{}'.format(maap_job.p_id, maap_job.job_id),
                                    headers = {'Authorization': 'Bearer '+ self.oauth_token})
            job_status = json.loads(response.content).get('status')
            #print(job_status)
            time.sleep(30)

        maap_job.status = job_status

    
    def write_outputs(self,maap_job, out_dir):

        if maap_job.status == 'SUCCEEDED':
            result_proc = requests.get('{}wpst/processes/{}/jobs/{}/result'.format(self.copa_backend_url, maap_job.p_id, maap_job.job_id), 
                               headers = {'Authorization': 'Bearer '+ self.oauth_token})
            json_res = json.loads(result_proc.content)
            
            os.makedirs(out_dir)
            
            if 'outputs' in json_res:
                for out in json_res['outputs']:
                    name = out['href'].split('?')[0].split('/')[-1]
                    r = requests.get(out['href'])
                    open(out_dir+'/'+name, 'wb').write(r.content)
    
    def delete_job(self,maap_job):
        requests.delete('{}wpst/processes/{}/jobs/{}'.format(self.copa_backend_url, maap_job.p_id, maap_job.job_id),
                        headers = {'Authorization': 'Bearer '+ self.oauth_token})
        
    def get_monitoring(self):
        """ Returns the monitoring info for the users"""
        result_proc = requests.get('{}wpst/processes/monitor'.format(self.copa_backend_url), 
                               headers = {'Authorization': 'Bearer '+ self.oauth_token})
        json_res = json.loads(result_proc.content)
        return json_res


        
