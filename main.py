import sys
import os
import SchedIO
import Task
import time
import threading
from Visualizer import create_graph

def delete_files_after_delay(file_paths, delay):
    """Delete the specified files after a delay in seconds."""
    time.sleep(delay)
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")
            else:
                print(f"File {file_path} does not exist.")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Use Schedsim "main.py" execution
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        scheduler = SchedIO.import_file(input_path, output_path)
        
        scheduler.execute()
        
        # Try the new implemented functionality
        
        # SPORADIC
        new_task = Task.Task(True, 'sporadic', 5, None, 15, 100, 5,"high",10)
        scheduler.new_task(new_task)

        # ADD_TIME
        scheduler.add_time(40)
        
        # PERIODIC
        new_task = Task.Task(True, 'periodic', 8, 10, None, 100, 5,"low",15)
        scheduler.new_task(new_task)
        
        # CREATE GRAPH
        output_image_path = 'visualizer/static/out2.png'
        create_graph(output_image_path, scheduler.start, scheduler.end, 1)
        
        # Delete the created temporany files
        file_to_delete = [output_image_path]
        delete_delay = 10
        print(f"Files will be deleted after {delete_delay} seconds...")
        deletion_thread = threading.Thread(target=delete_files_after_delay, args=(file_to_delete, delete_delay))
        deletion_thread.start()

    else:
        raise Exception(
            'Insufficient arguments. The name of the input and output files are required')
