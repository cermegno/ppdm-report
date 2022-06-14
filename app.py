from datetime import date, datetime, timedelta
import requests
import boto3
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

### PPDM details
ppdm_ip = "10.1.1.1"
username = "apireport"
password = ""
url_base = "https://" + ppdm_ip + ":8443/api/v2"
headers = {"content-type": "application/json"}
### TEAMS details - Create an "Incoming Webhoook" Connector for your Teams channel
teams_url = "https://dell.webhook.office.com/webhookb2/37934444-4444-4c20-9999-f94320b6/IncomingWebhook/47059377777"
### ECS details
ecs_host = "https://object.ecstestdrive.com"
access_key_id = 'mykey'
secret_key = 'mysecret'
bname = "PPDM" # Bucket name

verbose = 1 # 1=ON, 0=OFF

def login():
    '''login to PPDM and return the token'''

    url = url_base + "/login"
    data = {"username": username, "password": password}
    response = requests.post(url, headers=headers, json=data, verify=False)
    r_json = response.json()
    token = r_json["access_token"]

    return token

def get_1day_time():
    '''Return time string in PPDM friendly format for the time 24 hours ago '''

    gettime = datetime.now() - timedelta(days = 1)
    window = gettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return window

def get_activities():
    '''Get activities from PPDM REST API'''

    url = url_base + "/activities"
    window = get_1day_time()
    ### The API call also returns QUEUED and RUNNING activites that do not have a "result" key. So look for COMPLETED
    filt = 'classType in ("JOB", "JOB_GROUP") and category eq "PROTECT" and createdTime gt "{}" and state eq "COMPLETED"'.format(window)
    orderby = 'createTime DESC'
    pageSize = '10000'
    params = {'filter': filt, 'orderby': orderby, 'pageSize': pageSize}
    response = requests.get(url, headers=headers, params=params, verify=False)
    activities = response.json()['content']
    
    return activities

def get_failed_jobs(activities):
    '''Process activities JSON response and return information about failed jobs'''

    fail_report = []
    if verbose: print("Job Name","\t","Start Time","\t","Error Description")
    for a in activities:
        if a["result"]["status"] == "FAILED":
            if "error" in a["result"]:
                description = a["result"]["error"]["detailedDescription"]
            else:
                description = "No error description available for this job"
            fail_report.append({
                "name": a["name"],
                "startTime": a["startTime"],
                "description": description
                })
            if verbose: print(a["name"],a["startTime"],description)

    return fail_report

def get_job_summary(activities):
    '''Process activities JSON response and return a job summary'''

    j_ok = 0
    j_cancel = 0
    j_fail = 0

    for a in activities:
        if a["result"]["status"] == "OK":
            j_ok += 1
        if a["result"]["status"] == "FAILED":
            j_fail += 1
        if a["result"]["status"] == "CANCELED":
            j_cancel += 1
        
    if verbose: print("Successful Jobs: ",j_ok)
    if verbose: print("Failed Jobs: ",j_fail)
    if verbose: print("Canceled Jobs: ",j_cancel)
    if verbose: print("------------------------")

    summary = {
            "success": j_ok,
            "fail": j_fail,
            "cancel": j_cancel
            }

    return summary

def getConnection():
    ''' Create a connection with ECS and return S3 object'''
    
    secure = True
    s3 = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_key,
                      use_ssl=secure, endpoint_url=ecs_host)
    return s3

def upload_report():
    '''uploads file to ECS '''
    
    s3 = getConnection()
    args = {"ACL" : "public-read"}
    objectName = get_report_name()
    
    upload = s3.upload_file(objectName, bname, objectName, ExtraArgs=args, Callback=None)

    response = s3.list_objects_v2(Bucket = bname)
    for obj in response['Contents']:
        if verbose: print(obj['Key'], int(obj['Size']))

    return response


def get_report_name():
    '''create a report name based on today's date. Since report generattion is not implemented it returns a static report123.xlsx'''

    #Sample report name: ppdmsrv01-report-2022-05-25.xlsx
    today = date.today()
    report_file_name = "ppdmsrv01" + "-report-" + today.strftime("%Y-%m-%d") + ".xlsx"
    
    #return report_file_name
    return "report123.xlsx"


def generate_report(report_file_name):
    '''Not implemented yet - This will generate the detailed Excel report - We use report123.xlsx as a dummy'''

    return

def create_teams_payload():
    '''Assemble the payload for the POST call to Teams. There are 2 versions for the failed job section'''

    today = date.today()
    card_payload["text"] = "Backup report for ppdmsrv01.dps.spoc - " + today.strftime("%d/%B/%y")
    report_file_name = get_report_name()
    #generate_report(report_file_name) # This functionality hasn't been integrated yet. We use report123.xlsx as a dummy
    card_payload["potentialAction"][0]["targets"][0]["uri"] = "https://123456789.public.ecstestdrive.com/PPDM/" + report_file_name

    #Edit Summary section
    card_payload["sections"][0]["facts"][0]["value"] = summary["success"] 
    card_payload["sections"][0]["facts"][1]["value"] = summary["fail"] 
    card_payload["sections"][0]["facts"][2]["value"] = summary["cancel"]

    #Edit Fail Jobs section. This creates a table with details of the failed jobs 
    fail_report_section = {"activityTitle": "FAILED JOBS", "startGroup": True}
    ### Report with 2 colums
    fail_report_html = "<table style='width:100%'><th style='width:40%'>Job Name<th style='width:60%'>Description"
    for j in fail_report: 
        new_row = "<tr><td>" + j["name"] + "<td>" + j["description"]
        fail_report_html += new_row
    fail_report_html += "</table>"
    fail_report_section["text"] = fail_report_html
    card_payload["sections"].append(fail_report_section)

    return

# Teams card payload skeleton
card_payload = {
  "title": "PPDM Backup Report",
  "text": "Backup report for ppdmsrv01.dps.spoc",
  "sections": [
    {
      "activityTitle": "JOB SUMMARY",
      "facts": [
        {
          "name": "Successful Jobs",
          "value": 0
        },
        {
          "name": "Failed Jobs",
          "value": 0
        },
        {
          "name": "Canceled Jobs",
          "value": 0
        }
      ]
    }
  ],
  "potentialAction": [
    {
      "@type": "OpenUri",
      "name": "Download Full Report",
      "targets": [
        {
          "os": "default",
          "uri": "https://123456789.public.ecstestdrive.com/PPDM/report123.xlsx"
        }
      ]
    }
  ]
}


######################
#### MAIN SECTION ####
######################

token = login()
headers["Authorization"]= 'Bearer ' + token
activities = get_activities()
summary = get_job_summary(activities)

# No error checking here. It will fail if PPDM doesn't return any failed jobs
fail_report = get_failed_jobs(activities)

upload_report()

create_teams_payload()
if verbose: print(card_payload)

response = requests.post(teams_url, json=card_payload, verify=False)
if verbose: print(response)


