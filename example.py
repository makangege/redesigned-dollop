import requests
import time

def run_command(command):
    # Start the command
    response = requests.post('http://localhost:5000/execute', 
                           data={'command': command})
    process_id = response.json()['process_id']
    
    # Stream the output
    response = requests.get(f'http://localhost:5000/output/{process_id}', 
                          stream=True)
    
    for line in response.iter_lines():
        if line:
            print(line.decode())

# Example usage
if __name__ == '__main__':
    run_command('ping -c 5 google.com')
