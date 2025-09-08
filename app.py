from flask import Flask, Response, request
import subprocess
import threading
import queue
import time

app = Flask(__name__)

# Store running processes and their output queues
processes = {}

def read_output(process, q):
    """Read output from process and put it in the queue"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            q.put(output.strip())
    process.stdout.close()

@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.form.get('command')
    if not command:
        return {'error': 'No command provided'}, 400

    # Create a unique process ID
    process_id = str(time.time())
    
    # Create a queue for this process
    output_queue = queue.Queue()
    
    # Start the process
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )
    
    # Store process and queue
    processes[process_id] = {
        'process': process,
        'queue': output_queue
    }
    
    # Start output reader thread
    thread = threading.Thread(target=read_output, args=(process, output_queue))
    thread.daemon = True
    thread.start()
    
    return {'process_id': process_id}, 200

@app.route('/output/<process_id>')
def get_output(process_id):
    if process_id not in processes:
        return {'error': 'Process not found'}, 404

    def generate():
        while True:
            process_data = processes[process_id]
            process = process_data['process']
            q = process_data['queue']
            
            try:
                # Get output with timeout
                line = q.get(timeout=0.1)
                yield f"{line}\n"
            except queue.Empty:
                if process.poll() is not None:
                    # Process finished
                    del processes[process_id]
                    break
                continue
    
    return Response(generate(), mimetype='text/plain')

@app.route('/status/<process_id>')
def get_status(process_id):
    if process_id not in processes:
        return {'error': 'Process not found'}, 404
        
    process = processes[process_id]['process']
    return {
        'running': process.poll() is None,
        'exit_code': process.poll()
    }

if __name__ == '__main__':
    app.run(debug=True)
