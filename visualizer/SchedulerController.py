from flask import Flask, render_template, request, jsonify
import os
import sys
import matplotlib
import xml.etree.ElementTree as ET
import xml.dom.minidom

matplotlib.use('Agg')  

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import SchedIO
import Task
from Visualizer import create_graph

app = Flask(__name__)

class SchedulerController:
    def __init__(self):
        self.scheduler = None
        self.output_file = 'input/out.csv'
        self.input_file = None
        self.end = 0
        self.start = 0
    
    # Method to load an XML file and initialize the scheduler
    # @input: file_path (str) - The path to the XML file
    # @output: bool - True if the file is successfully loaded, False if the file is not found
    def load_xml_file(self, file_path):
        self.input_file = file_path
        try:
            self.scheduler = SchedIO.import_file(file_path, self.output_file)
            self.end = self.scheduler.end
            self.start = self.scheduler.start

            return True
        except FileNotFoundError:
            print("File not found.")
            return False

    def execute_scheduler(self):
        if self.scheduler:
            self.scheduler.execute()
            self.scheduler.terminate()
            return True
        else:
            print("Scheduler not loaded.")
            return False

    def create_task(self, task_data):
        if self.scheduler:
            if task_data[1] == 'sporadic':
                n_task = Task.Task(task_data[0], task_data[1], task_data[2], None, task_data[3], task_data[4], task_data[5])
            elif task_data[1] == 'periodic':
                n_task = Task.Task(task_data[0], task_data[1], task_data[2], task_data[3], None, task_data[4], task_data[5])
            self.scheduler.new_task(n_task)
            self.scheduler.terminate()
            return True
        else:
            print("Scheduler not loaded.")
            return False

    def add_new_time(self, n_time):
        if self.scheduler:
            self.scheduler.add_time(n_time)
            self.end = self.end + n_time
            self.scheduler.terminate()
            return True
        else:
            print("Scheduler not loaded.")
            return False
        
    def print_graph(self, start, end, fraction):
        try:
            # Check if the output file exist, or lunch an exeception
            if not os.path.exists('input/out.csv'):
                raise FileNotFoundError("out.csv file not found.")
            create_graph('static/out.png', start, end, fraction)
            return True
        except Exception as e:
            print(f"Error printing graph: {str(e)}")
            return False

    def create_xml(self, file_path, start, end, tasks, scheduling_algorithm, cpu_pe_id, cpu_speed,quantum):
        try:
            # Creating the XML document
            doc = xml.dom.minidom.Document()
            simulation = doc.createElement("simulation")
            doc.appendChild(simulation)

            # Adding the node for simulation time
            time = doc.createElement("time")
            time.setAttribute("start", str(start))
            time.setAttribute("end", str(end))
            simulation.appendChild(time)

            # Adding the node for software (tasks and scheduler)
            software = doc.createElement("software")
            simulation.appendChild(software)

            tasks_node = doc.createElement("tasks")
            software.appendChild(tasks_node)

            # Adding nodes for each task
            for task_data in tasks:
                task = doc.createElement("task")
                for key, value in task_data.items():
                    # Ensure the value is not None before converting it to a string
                    if value is not None:
                        task.setAttribute(key, str(value))
                tasks_node.appendChild(task)

            # Adding the node for scheduler
            scheduler = doc.createElement("scheduler")
            scheduler.setAttribute("algorithm", scheduling_algorithm)
            if scheduling_algorithm == "RR":
                scheduler.setAttribute("quantum", str(quantum))
            software.appendChild(scheduler)

            # Adding the node for hardware
            hardware = doc.createElement("hardware")
            simulation.appendChild(hardware)

            cpus = doc.createElement("cpus")
            hardware.appendChild(cpus)

            pe = doc.createElement("pe")
            pe.setAttribute("id", str(cpu_pe_id))
            pe.setAttribute("speed", str(cpu_speed))
            cpus.appendChild(pe)

            # Writing the XML document to file
            with open(file_path, "w", encoding="utf-8") as xml_file:
                doc.writexml(xml_file, indent="\t", newl="\n", addindent="\t", encoding="utf-8")

            return file_path
        except Exception as e:
            print(f"Error creating XML file: {str(e)}")
            return None