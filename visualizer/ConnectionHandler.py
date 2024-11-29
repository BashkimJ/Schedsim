import tempfile
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import sys
import matplotlib
from SchedulerController import SchedulerController

matplotlib.use('Agg') 

# The path to use the class of Scheduler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import SchedIO
import Task
from Visualizer import create_graph

app = Flask(__name__)
# Create the object "Scheduler" to control the web request 
scheduler_controller = SchedulerController()

@app.route('/')
def index():
    return render_template('index.html', title='schedsim')

@app.route('/upload_xml', methods=['POST'])
def upload_xml():
    if 'xmlFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    xml_file = request.files['xmlFile']
    if xml_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    save_path = os.path.join("input", xml_file.filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    xml_file.save(save_path)
    success = scheduler_controller.load_xml_file(save_path)
    if success:
        return jsonify({'message': 'XML File uploaded successfully!', 'file_path': save_path}), 200
    else:
        return jsonify({'error': 'Error loading XML file.'}), 500

@app.route('/execute_main', methods=['POST'])
def execute_main():
    try:
        #scheduler_controller.load_xml_file(scheduler_controller.input_file)
        success = scheduler_controller.execute_scheduler()
        if not success:
            return jsonify({"error": "Error executing scheduler"}), 500

        return jsonify({"output": "Execution completed!"}), 200

    except Exception as e:
        # Generic handling for other errors
        error_message = f"An unexpected error occurred: {str(e)}"
        app.logger.error(error_message)
        return jsonify({"error": error_message}), 500

    finally:
        # Delete the input file if it exists
        try:
            if scheduler_controller.input_file and os.path.exists(scheduler_controller.input_file):
                os.remove(scheduler_controller.input_file)
        except Exception as e:
            app.logger.error(f"Error occurred while deleting the file: {str(e)}")

@app.route('/create_task', methods=['POST'])
def create_task():
    # Receive form data to create a new task
    real_time = request.form.get('realTime')
    task_type = request.form.get('taskType')
    task_id = request.form.get('taskId')
    period = request.form.get('period')
    activation = request.form.get('activation')
    deadline = request.form.get('deadline')
    wcet = request.form.get('wcet')
    wcet_high = request.form.get('wcet_high')
    criticality = request.form.get('criticality')
    if task_type=='periodic':
        if not all([real_time, task_type, task_id, period, deadline, wcet,wcet_high,criticality]):
            return jsonify({'error': 'All fields are required.'}), 400
    elif task_type=='sporadic':
        if not all([real_time, task_type, task_id, activation, deadline, wcet,wcet_high,criticality]):
            return jsonify({'error': 'All fields are required.'}), 400
    
    # Convert values to appropriate types
    try:
        task_id = int(task_id)
        real_time = bool(real_time)
        if task_type=='periodic':
            period = int(period)
            activation=0
        if task_type=='sporadic':
            activation = int(activation)
            period=0
        deadline = int(deadline)
        wcet = int(wcet)
        wcet_high = int(wcet_high)
    except ValueError:
        return jsonify({'error': 'Invalid input format.'}), 400
    # Perform additional checks on the values
    if task_id <= 0:
        return jsonify({'error': 'Task ID must be a positive integer.'}), 400
    if wcet <= 0 | wcet_high<=0 :
        return jsonify({'error': 'WCET and WCET_HIGH must be a positive integer.'}), 400
    if (task_type == 'periodic' and period <= 0) or (task_type == 'sporadic' and activation < 0):
        return jsonify({'error': 'Invalid period or activation value.'}), 400
    if deadline <= 0:
        return jsonify({'error': 'Deadline must be a positive integer.'}), 400
    if wcet > period and task_type == 'periodic':
        return jsonify({'error': 'WCET must be less than or equal to period.'}), 400
    if deadline < wcet:
        return jsonify({'error': 'Deadline must be greater than WCET.'}), 400
    if wcet_high<wcet | wcet_high>deadline:
        return jsonify({'error':'WCET_HIGH must be greater than WCET and lower than Deadline'})
    if not real_time and (scheduler_controller.scheduler.name == "OBCP" or scheduler_controller.scheduler.name == "EDF-VD"):
        return jsonify({'error':'Non real-time tasks in EDF-VD and OBCP are not accepted'})


    
    print(f'Real Time: {real_time}, Task Type: {task_type}, Task ID: {task_id}, Period: {period}, Activation: {activation}, Deadline: {deadline}, WCET: {wcet},WCET_HIGH:{wcet_high},Criticality:{criticality}')
    
    if task_type == "sporadic":
        success = scheduler_controller.create_task([real_time, task_type, task_id, activation, deadline, wcet,criticality,wcet_high])
    elif task_type == "periodic":
        success = scheduler_controller.create_task([real_time, task_type, task_id, period, activation, deadline, wcet,criticality,wcet_high])
    if success:
        return jsonify({'message': 'Task created successfully!'}), 200
    else:
        return jsonify({'error': 'Error creating task.'}), 500

@app.route('/print_graph', methods=['POST'])
def print_graph():
    try:
        data = request.get_json()
        
        if data.get('use_fixed_params'):
            start_time = scheduler_controller.start  
            end_time = scheduler_controller.end  
            fraction_time = 1  
        else:
            # Get parameters from the request
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            fraction_time = data.get('frac_time')
        # Validations
        if start_time is None or end_time is None or fraction_time is None:
            return jsonify({'error': 'Missing parameters.'}), 400

        if not isinstance(start_time, int) or start_time < 0:
            return jsonify({'error': 'Start time must be a positive integer.'}), 400

        if not isinstance(end_time, int) or end_time <= start_time:
            return jsonify({'error': 'End time must be an integer greater than start time.'}), 400

        if scheduler_controller.end is not None and end_time > scheduler_controller.end:
            return jsonify({
                'error': f'The end time should not be greater than scheduler end {scheduler_controller.end}'}), 400
        
        if not isinstance(fraction_time, int) or not (1 <= fraction_time <= 5):
            return jsonify({'error': 'Fraction time must be an integer between 1 and 5.'}), 400

        success = scheduler_controller.print_graph(start_time, end_time, fraction_time)
        if success:
            return jsonify({'message': 'Graph printed successfully!'}), 200
        else:
            return jsonify({'error': 'Error printing graph.'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_xml', methods=['GET'])
def download_xml():
    try:
        temp_dir = tempfile.gettempdir()
        filename = 'temp.xml'
        file_path = os.path.join(temp_dir, filename)
        
        if os.path.exists(file_path):
            
            return send_file(file_path, as_attachment=True, mimetype='application/xml')
        else:
            return jsonify({'error': 'File not found.'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_csv', methods=['GET'])
def download_csv():
    try:
        temp_dir = tempfile.gettempdir()
        filename = 'out.csv'
        file_path = os.path.join(temp_dir, filename)
        if os.path.exists(file_path):
            
            return send_file(file_path, as_attachment=True, mimetype='text/csv')
        else:
            return jsonify({'error': 'File not found.'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit_all_tasks', methods=['POST'])
def submit_all_tasks():
    try:
        data = request.get_json()
        print(len(data))
        total_task = int((len(data)-4)/9)
        
        start = int(data[0])
        end = int(data[1])
        scheduling_algorithm = data[2]
        if scheduling_algorithm == "RR":
            quantum = int(data[3])
        elif scheduling_algorithm == "OBCP" or scheduling_algorithm=="EDF-VD":
            policy = data[3]
        else:
            quantum = 0
        pos = 4
        tasks = []
        
        for i in range(total_task):
            real_time = data[pos]
            task_type = data[pos+1]
            task_id = data[pos+2]
            period = data[pos+3]
            activation = data[pos+4] 
            deadline = data[pos+5]
            wcet = data[pos+6]
            wcet_high = data[pos+7]
            criticality = data[pos+8]
            pos += 9

            if task_type=='periodic':
                if not all([real_time, task_type, task_id, period, deadline, wcet]):
                    return jsonify({'error': 'All fields are required.'}), 400
            elif task_type=='sporadic':
                if not all([real_time, task_type, task_id, activation, deadline, wcet]):
                    return jsonify({'error': 'All fields are required.'}), 400
            # Convert values to appropriate types
            try:
                task_id = int(task_id)
                real_time = bool(real_time)
                if task_type=='periodic':
                    period = int(period)
                    activation=0
                if task_type=='sporadic':
                    activation = int(activation)
                    period=0
                deadline = int(deadline)
                wcet = int(wcet)
                wcet_high = int(wcet_high)
            except ValueError:
                return jsonify({'error': 'Invalid input format.'}), 400

            # Perform additional checks on the values
            if task_id <= 0:
                return jsonify({'error': 'Task ID must be a positive integer.'}), 400
            if wcet <= 0 & wcet_high<=0:
                return jsonify({'error': 'WCET and WCET_HIGH must be a positive integer.'}), 400
            if (task_type == 'periodic' and period <= 0) or (task_type == 'sporadic' and activation < 0):
                return jsonify({'error': 'Invalid period or activation value.'}), 400
            if deadline <= 0:
                return jsonify({'error': 'Deadline must be a positive integer.'}), 400
            if task_type == 'periodic' and wcet > period :
                return jsonify({'error': 'WCET must be less than or equal to period.'}), 400
            if deadline < wcet & deadline<wcet_high:
                return jsonify({'error': 'Deadline must be greater than WCET and WCET_HIGH.'}), 400
            if wcet_high<=wcet:
                return jsonify({'error':'WCET_HIGH must be greater than WCET.'}), 400
            if scheduling_algorithm == "RR" and quantum < 0:
                return jsonify({'error': 'Quantum must be greater than 0.'}), 400
            if start < 0:
                return jsonify({'error': 'Start must be greater than 0.'}), 400
            if end < 0 and start > end:
                return jsonify({'error': 'End must be greater than 0 and higher than start.'}), 400
            
            if task_type == 'periodic':
                task = {
                    "real_time": real_time,
                    "type": task_type,
                    "id": task_id,
                    "period": period,
                    "deadline": deadline,
                    "wcet": wcet,
                    "criticality": criticality,
                    "wcet_high":wcet_high

                }
            elif task_type == 'sporadic':
                task = {
                    "real_time": real_time,
                    "type": task_type,
                    "id": task_id,
                    "activation": activation,
                    "deadline": deadline,
                    "wcet": wcet,
                    "criticality": criticality,
                    "wcet_high": wcet_high

                }
            tasks.append(task)


        # Get the temporary directory path
        temp_dir = tempfile.gettempdir()

        # Add the file name "temp.xml" to the temporary directory path
        temp_file_path = os.path.join(temp_dir, "temp.xml")
        # Execute XML file creation using SchedulerController's create_xml method
        xml_path = scheduler_controller.create_xml(temp_file_path, int(start), int(end), tasks, scheduling_algorithm, 0, 1, quantum,policy)

        if xml_path:
            return jsonify({'message': 'XML file created successfully!', 'xml_path': xml_path}), 200
        else:
            return jsonify({'error': 'Failed to create XML file.'}), 500
        
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        app.logger.error(error_message)
        return jsonify({"error": error_message}), 500
    
@app.route('/add_time', methods=['POST'])
def add_time():
    try:
        data = request.get_json()
        new_time = data.get('new_time')

        if new_time is None or not isinstance(new_time, int):
            return jsonify({'error': 'Invalid or missing new_time parameter.'}), 400

        success = scheduler_controller.add_new_time(new_time)
        if success:
            return jsonify({'message': 'New time added successfully!'}), 200
        else:
            return jsonify({'error': 'Error adding new time.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
