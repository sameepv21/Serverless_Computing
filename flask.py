from flask import Flask,request,Response,make_response
import subprocess
import json
import requests
import time
import os

app = Flask(__name__)


@app.route('/ping')
def ping():
    return 'pong'

@app.route('/getinfo', methods=['GET'])
def get_info():
    job_id = "--all"
    req_data = False
    if(request.data):
        req_data = request.get_json(force=True) 
    if(req_data):
        job_id = req_data["job_id"]

    result = subprocess.run(['multipass', 'info', job_id], stdout=subprocess.PIPE)
    print("job get info",job_id)

    # Convert the output of the command to a dictionary object
    output = result.stdout.decode('utf-8')
    print("Output",output)
    data = []
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            data.append({key.strip(): value.strip()})

    # Create a nested dictionary using the data from the 'multipass info --all' command
    nested_data = {}
    instance_count = 0
    for item in data:
        for key, value in item.items():
            if key == 'Name':
                instance_count += 1
                instance_key = 'Instance_{}'.format(instance_count)
                nested_data[instance_key] = {}
            else:
                nested_data[instance_key][key] = value

    # Add the "count" value to the nested dictionary
    nested_data['count'] = instance_count

    # Convert the nested dictionary to a JSON string
    json_result = json.dumps(nested_data)
    
    return Response(json_result, mimetype="application/json")

    # Return the JSON string as the response

def updateInstaneToRunning(job_id):
    
    print("running uitr",job_id)
    
    getInfoUrl = "http://localhost:5000/getinfo"
    getInfoData= {"job_id":job_id}
    time.sleep(2)
    infoResponseRaw = requests.get(getInfoUrl,data=getInfoData)
    infoResponse = infoResponseRaw.json()
    print("infoResponse",infoResponse)
    print("memory",infoResponse["Instance_1"]["Memory usage"])
    # print("rawJson",infoResponseJson)
    # infoResponse = json.loads(infoResponseJson)
    print("yo",infoResponse,infoResponse["Instance_1"]["Memory usage"], infoResponse["Instance_1"]["Disk usage"])
    
    url = "http://10.1.28.171:8000/update_to_running/"
    data = {"job_id":job_id,"memory_usage":infoResponse["Instance_1"]["Memory usage"],"disk_usage":infoResponse["Instance_1"]["Disk usage"]}
    
    response = requests.post(url,data=data)
    
    
@app.route('/redirect',methods=['GET'])
def redir():
    job_id = request.args.get('job_id')
    print("time sleep activated")
    updateInstaneToRunning(job_id)
    return "hello"


@app.route('/create',methods=['POST'])
def terminal():
    print("RD",request)
    print("RDData",request.data)
    req_data = False

    if(request.data):
        req_data = request.get_json(force=True) 
    if(req_data):
        job_id = req_data["job_id"]
    else:
        return "none"
    
    print("job_id create",job_id)
    # Start a subprocess to run a command in the terminal
    proc = subprocess.Popen(["multipass", "launch", "-n",job_id], stdout=subprocess.PIPE)
    
    proc.communicate()


    # Set up a generator function to yield the command's output in real-time
    def realtime_output():
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            yield line
    
    # realtime_output = proc.stdout.decode('utf-8')
    
    response = make_response(realtime_output())
    
    # Set additional headers or cookies on the response
    response.headers['X-Custom-Header'] = 'Custom Value'
    
    # Send the response to the client
    requests.get("http://0.0.0.0:5000/redirect?job_id="+job_id)
    return response

    # Return the real-time output as a streaming response
    # return Response(realtime_output(), mimetype="text/plain")



def updateInstanceToCompleted(job_id,output):
    url = "http://10.1.28.171:8000/update_to_completed/"
    data = {"job_id":job_id,"output":output}
    response = requests.post(url,data=data)    
    
    

@app.route('/python', methods=['GET'])
def index():
    # Get the "name" query parameter from the request
    file_path = request.args.get('file_path')
    file_name = request.args.get('file_name')
    job_id = request.args.get('job_id')
    
    wget_command = "wget " + file_path
    run_command = "python3 " + file_name
    rm_command = "rm -rf " + file_name
    
    os.system(wget_command)
    save_output = os.popen(run_command).read()
    os.system(rm_command)
    
    
    updateInstanceToCompleted(job_id, str(save_output))

    print(save_output)

    return(save_output)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)



import time
from multipass import Multipass

# Create a Multipass instance
mp = Multipass()

# Set the threshold for server usage (80%)
threshold = 80

# Set the time interval to check for server usage (5 minutes)
interval = 5 * 60

while True:
  # Get the current server usage
  usage = mp.server_usage()

  # Check if the server usage is above the threshold
  if usage > threshold:
    # Check if the server has been above the threshold for more than 5 minutes
    if time.time() - mp.last_high_usage_time > interval:
      # Run the specified multipass commands to scale the server
      mp.run_command("multipass set local.servername.cpus=4")
      mp.run_command("multipass set local.servername.disk=60G")
      mp.run_command("multipass set local.servername.memory=7G")

  # Sleep for 1 second before checking again
  time.sleep(1)
