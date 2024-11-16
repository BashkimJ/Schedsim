import xml.etree.ElementTree as ET
import SchedIO
import Task
import random

MAX_TIME_START = 20
MAX_TIME_END = 100
MAX_PERIOD = 40
MAX_WCET = 20
MAX_QUANTUM = 10
TASKS_NUMS = 10
NEW_TASKS_NUMS = 4

def compare_files(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content_file1 = f1.read()
        content_file2 = f2.read()
    if content_file1 == content_file2:
        print("Correct")
    else:
        print("Not correct")

if __name__ == "__main__":
    alg = random.randint(0, 6)
    if alg == 0:
        scheduling_algorithm = "FIFO"
    if alg == 1:
        scheduling_algorithm = "SJF"
    if alg == 2:
        scheduling_algorithm = "HRRN"
    if alg == 3:
        scheduling_algorithm = "SRTF"
    if alg == 4:
        scheduling_algorithm = "RR"
    time_start = random.randint(0, MAX_TIME_START)
    time_end = random.randint(time_start + 1, MAX_TIME_END)
    add_time = random.randint(1, MAX_TIME_END)
    simulation1 = ET.Element("simulation")
    time1 = ET.SubElement(simulation1, "time", start=str(time_start), end=str(time_end + add_time))
    time1.tail = "\n"
    software1 = ET.SubElement(simulation1, "software")
    tasks1 = ET.SubElement(software1, "tasks")
    tasks1.tail = "\n"
    simulation2 = ET.Element("simulation")
    time2 = ET.SubElement(simulation2, "time", start=str(time_start), end=str(time_end))
    time2.tail = "\n"
    software2 = ET.SubElement(simulation2, "software")
    tasks2 = ET.SubElement(software2, "tasks")
    tasks2.tail = "\n"
    new_tasks = []

    for task in range(1, TASKS_NUMS + 1):
        real_time = random.randint(0, 1)
        real_time_str = ''
        if real_time == 0:
            real_time = False
            real_time_str = 'false'
        else:
            real_time = True
            real_time_str = 'true'
        type = random.randint(0, 1)
        activation = None
        period = None
        deadline = None
        wcet = None
        if type == 0:
            type = 'sporadic'
            activation = random.randint(time_start, time_end - 1)
            deadline = random.randint(activation + 1, MAX_TIME_END)
            wcet = random.randint(1, max(1, deadline - 1))
        else:
            type = 'periodic'
            period = random.randint(1, MAX_PERIOD)
            deadline = random.randint(time_start + 1, MAX_TIME_END)
            wcet = random.randint(1, max(1, min(period, deadline)))
        id = task
        if type == 'sporadic':
            if real_time:
                add_task1 = ET.SubElement(tasks1, "task", real_time=real_time_str, type="sporadic", id=str(id), activation=str(activation), deadline=str(deadline), wcet=str(wcet))
                add_task1.tail = "\n"
                if task <= TASKS_NUMS - NEW_TASKS_NUMS:
                    add_task2 = ET.SubElement(tasks2, "task", real_time=real_time_str, type="sporadic", id=str(id), activation=str(activation), deadline=str(deadline), wcet=str(wcet))
                    add_task2.tail = "\n"
                else:
                    new_task = Task.Task(real_time, type, task, None, activation, deadline, wcet)
                    new_tasks.append(new_task)
            else:
                add_task1 = ET.SubElement(tasks1, "task", real_time=real_time_str, type="sporadic", id=str(id), activation=str(activation), wcet=str(wcet))
                add_task1.tail = "\n"
                if task <= TASKS_NUMS - NEW_TASKS_NUMS:
                    add_task2 = ET.SubElement(tasks2, "task", real_time=real_time_str, type="sporadic", id=str(id), activation=str(activation), wcet=str(wcet))
                    add_task2.tail = "\n"
                else:
                    new_task = Task.Task(real_time, type, task, None, activation, deadline, wcet)
                    new_tasks.append(new_task)
        else:
            add_task1 = ET.SubElement(tasks1, "task", real_time=real_time_str, type="periodic", id=str(id), period=str(period), deadline=str(deadline), wcet=str(wcet))
            add_task1.tail = "\n"
            if task <= TASKS_NUMS - NEW_TASKS_NUMS:
                add_task2 = ET.SubElement(tasks2, "task", real_time=real_time_str, type="periodic", id=str(id), period=str(period), deadline=str(deadline), wcet=str(wcet))
                add_task2.tail = "\n"
            else:
                new_task = Task.Task(real_time, type, task, period, None, deadline, wcet)
                new_tasks.append(new_task)
    if scheduling_algorithm != "RR":
        scheduler1 = ET.SubElement(software1, "scheduler", algorithm=scheduling_algorithm)
        scheduler1.tail = "\n"
        scheduler2 = ET.SubElement(software2, "scheduler", algorithm=scheduling_algorithm)
        scheduler2.tail = "\n"
    else:
        quantum = random.randint(1, MAX_QUANTUM)
        scheduler1 = ET.SubElement(software1, "scheduler", algorithm=scheduling_algorithm, quantum=str(quantum))
        scheduler1.tail = "\n"
        scheduler2 = ET.SubElement(software2, "scheduler", algorithm=scheduling_algorithm, quantum=str(quantum))
        scheduler2.tail = "\n"
    hardware1 = ET.SubElement(simulation1, "hardware")
    hardware2 = ET.SubElement(simulation2, "hardware")
    cpus1 = ET.SubElement(hardware1, "cpus")
    cpus1.tail = "\n"
    cpus2 = ET.SubElement(hardware2, "cpus")
    cpus2.tail = "\n"
    pe1 = ET.SubElement(cpus1, "pe", id="0", speed="1")
    pe1.tail = "\n"
    pe2 = ET.SubElement(cpus2, "pe", id="0", speed="1")
    pe2.tail = "\n"
    tree1 = ET.ElementTree(simulation1)
    tree1.write("examples/Inputs/test_input1.xml", encoding="UTF-8", xml_declaration=True)
    tree2 = ET.ElementTree(simulation2)
    tree2.write("examples/Inputs/test_input2.xml", encoding="UTF-8", xml_declaration=True)

    test_scheduler1 = SchedIO.import_file("examples/Inputs/test_input1.xml", "examples/Outputs/test_output1.csv")
    test_scheduler1.execute()
    test_scheduler1.terminate()
    test_scheduler2 = SchedIO.import_file("examples/Inputs/test_input2.xml", "examples/Outputs/test_output2.csv")
    test_scheduler2.execute()

    count = 0
    for new_task in new_tasks:
        test_scheduler2.new_task(new_task)
        test_scheduler2.terminate()
        count += 1
    test_scheduler2.add_time(add_time)
    test_scheduler2.terminate()

    compare_files("examples/Outputs/test_output1.csv", "examples/Outputs/test_output2.csv")
