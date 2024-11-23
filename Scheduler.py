import math
import copy
from abc import *

from nltk.classify.maxent import calculate_nfmap

import SchedEvent
import SchedIO
from functools import reduce


class Scheduler:

    def __init__(self, output_file):
        self.name = 'GenericScheduler'
        self.tasks = []
        self.start = None
        self.end = None

        self.executing = None

        self.arrival_events = []
        self.finish_events = []
        self.deadline_events = []
        self.start_events = []

        self.starting_arrivals = []
        self.size = 0
        self.time_list = []
        self.arrival_events_list = []
        self.finish_events_list = []
        self.deadline_events_list = []
        self.start_events_list = []
        self.executing_list = []

        self.quantum_counter_at_time = []

        self.quantum_counter_list = []

        self.output_file = SchedIO.SchedulerEventWriter(output_file)

        self.cores = []

        self.event_id = 0


        self.mode = "low"
        #Coefficent to mult the deadline during the EDF-VD algorythm. To be calculated
        self.x = 0

        self.policy = None

        self.hyperperiod = None



    @abstractmethod
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def find_finish_events(self, time):
        pass

    def get_all_arrivals(self):
        arrival_events = []
        for task in self.tasks:
            # Here you can add the code to choose between different cores:
            task.core = self.cores[0].id
            # ------------------------------- #
            if task.type == 'periodic':
                i = self.start
                j = 1
                while i < self.end:
                    event = SchedEvent.ScheduleEvent(i, task, SchedEvent.EventType.activation.value, self.event_id)
                    self.event_id += 1
                    event.job = j
                    arrival_events.append(event)
                    i += task.period
                    j += 1
            elif task.type == 'sporadic':
                task.init = task.activation
                event = SchedEvent.ScheduleEvent(task.activation, task, SchedEvent.EventType.activation.value, self.event_id)
                self.event_id += 1
                arrival_events.append(event)
        arrival_events.sort(key=lambda x: x.timestamp)
        return arrival_events

    def add_arrivals(self, time_start, time_end):
        for task in self.tasks:
            task.core = self.cores[0].id
            if task.type == 'periodic':
                i = self.start
                j = 1
                while i < time_end:
                    if i >= time_start:
                        event = SchedEvent.ScheduleEvent(i, task, SchedEvent.EventType.activation.value, self.event_id)
                        self.event_id += 1
                        event.job = j
                        for arrival_events in self.arrival_events_list:
                            arrival_events.append(copy.deepcopy(event))
                            arrival_events.sort(key=lambda x: x.timestamp)
                    i += task.period
                    j += 1

    def find_arrival_event(self, time):
        helper_list = []
        for event in self.arrival_events:
            if event.timestamp == time:
                self.output_file.add_scheduler_event(event)
                start_event = SchedEvent.ScheduleEvent(
                    event.timestamp, event.task, SchedEvent.EventType.start.value, event.id)
                start_event.job = event.job
                self.start_events.append(start_event)
            elif event.timestamp > time:
                helper_list.append(event)
        self.arrival_events = helper_list

    def find_deadline_events(self, time):
        helper_list = []
        for event in self.deadline_events:
            if event.timestamp == time:
                self.output_file.add_scheduler_event(event)
            elif event.timestamp > time:
                helper_list.append(event)
        self.deadline_events = helper_list


class NonPreemptive(Scheduler):

    def __init__(self, output_file):
        super().__init__(output_file)
        self.name = 'GenericNonPreemptiveScheduler'

    def execute(self):
        pass

    def find_finish_events(self, time):
        helper_list = []
        for event in self.finish_events:
            if event.timestamp == time:
                self.output_file.add_scheduler_event(event)
                self.executing = None
            elif event.timestamp > time:
                helper_list.append(event)
        self.finish_events = helper_list

    def find_start_events(self, time):
        helper_list = []
        for event in self.start_events:
            if event.timestamp == time and self.executing is None:
                self.output_file.add_scheduler_event(event)
                self.executing = event
                # Create finish event:
                finish_timestamp = event.timestamp + event.task.wcet
                finish_event = SchedEvent.ScheduleEvent(
                    finish_timestamp, event.task, SchedEvent.EventType.finish.value, event.id)
                finish_event.job = event.job
                self.finish_events.append(finish_event)
                # Create deadline event:
                if event.task.real_time:
                    deadline_timestamp = event.timestamp + event.task.deadline
                    deadline_event = SchedEvent.ScheduleEvent(
                        deadline_timestamp, event.task, SchedEvent.EventType.deadline.value, event.id)
                    deadline_event.job = event.job
                    self.deadline_events.append(deadline_event)
            elif event.timestamp == time and self.executing:
                event.timestamp += (self.executing.timestamp + self.executing.task.wcet - event.timestamp)
            if event.timestamp > time:
                helper_list.append(event)
        self.start_events = helper_list


class Preemptive(Scheduler):

    def __init__(self, output_file):
        super().__init__(output_file)
        self.name = 'GenericPreemptiveScheduler'

    def execute(self):
        pass

    def find_finish_events(self, time):
        if self.executing:
            if self.executing.executing_time == self.executing.task.wcet:
                # Create finish event:
                finish_event = SchedEvent.ScheduleEvent(
                    time, self.executing.task, SchedEvent.EventType.finish.value, self.executing.id)
                finish_event.job = self.executing.job
                self.output_file.add_scheduler_event(finish_event)
                # Delete from start_events:
                for event in self.start_events:
                    if event.id == self.executing.id:
                        self.start_events.remove(event)
                #self.start_events.remove(self.executing)
                # Free execute:
                self.executing = None

    def create_deadline_event(self, event):
        if event.task.real_time:
            deadline_timestamp = event.timestamp + event.task.deadline
            deadline_event = SchedEvent.ScheduleEvent(
                deadline_timestamp, event.task, SchedEvent.EventType.deadline.value, event.id)
            deadline_event.job = event.job
            self.deadline_events.append(deadline_event)
            event.task.first_time_executing = False

def search_pos(self, time):
    for i in range(len(self.time_list) - 1):
        if self.time_list[i] <= time and self.time_list[i + 1] > time:
            return i
    return len(self.time_list) - 1

def delete(self, time):
    if(self.time_list[-1] >= time):
        self.time_list.pop()
        self.arrival_events_list.pop()
        self.finish_events_list.pop()
        self.deadline_events_list.pop()
        self.start_events_list.pop()
        self.executing_list.pop()
        if self.name == 'RoundRobin':
            self.quantum_counter_list.pop()
        delete(self, time)

def reset(self):
    self.executing = None
    self.finish_events = []
    self.deadline_events = []
    self.arrival_events = []
    self.start_events = []
    self.time_list = []
    self.finish_events_list = []
    self.deadline_events_list = []
    self.arrival_events_list = []
    self.start_events_list = []
    self.executing_list = []
    if self.name == 'ShortestRemainingTimeFirst' or self.name == 'RoundRobin':
        for task in self.tasks:
            task.first_time_executing = True
            task.finish = False
    if self.name == 'RoundRobin':
        self.quantum_counter = 0
        self.quantum_counter_list = []


class FIFO(NonPreemptive):

    def __init__(self, output_file):
        super().__init__(output_file)
        self.name = 'FIFO'

    def compute(self, time, count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            self.find_start_events(time)

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                count = 0
            time += 1

    def execute(self):
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        count = self.size - 1
        time = self.start
        self.compute(time, count)

    def new_task(self, new_task):
        time = self.start
        count = 0
        new_task.core = self.cores[0].id
        if new_task.type == 'sporadic' and new_task.activation > self.start:
            time = new_task.activation
            pos = search_pos(self, time - 1)
            self.finish_events = copy.deepcopy(self.finish_events_list[pos])
            self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
            self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
            self.start_events = copy.deepcopy(self.start_events_list[pos])
            self.executing = copy.deepcopy(self.executing_list[pos])
            self.tasks.append(new_task)
            new_task.init = new_task.activation
            event = SchedEvent.ScheduleEvent(new_task.activation, new_task, SchedEvent.EventType.activation.value, self.event_id)
            self.event_id += 1
            for p in range(pos + 1):
                self.arrival_events_list[p].append(copy.deepcopy(event))
                self.arrival_events_list[p].sort(key=lambda x: x.timestamp)
            self.arrival_events.append(copy.deepcopy(event))
            self.arrival_events.sort(key=lambda x: x.timestamp)
            time = self.time_list[pos] + 1
            delete(self, time)
        else:
            reset(self)
            self.tasks.append(new_task)
            self.arrival_events = self.get_all_arrivals()
            count = self.size - 1
        self.output_file.clean(time)
        self.compute(time, count)

    def add_time(self, add_time):
        self.add_arrivals(self.end, self.end + add_time)
        pos = search_pos(self, self.end - 1)
        self.finish_events = copy.deepcopy(self.finish_events_list[pos])
        self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
        self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
        self.start_events = copy.deepcopy(self.start_events_list[pos])
        self.executing = copy.deepcopy(self.executing_list[pos])
        self.end += add_time
        time = self.time_list[pos] + 1
        delete(self, time)
        self.output_file.clean(time)
        self.compute(time, self.start)

    def terminate(self):
        self.output_file.terminate_write()


class SJF(NonPreemptive):

    def __init__(self, output_file):
        super().__init__(output_file)
        self.name = 'SJF'

    def compute(self, time, count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            # Sort by wcet:
            self.start_events.sort(key=lambda x: x.task.wcet)
            self.find_start_events(time)

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                count = 0
            time += 1

    def execute(self):
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        count = self.size - 1
        time = self.start
        self.compute(time, count)

    def new_task(self, new_task):
        time = self.start
        count = 0
        new_task.core = self.cores[0].id
        if new_task.type == 'sporadic' and new_task.activation > self.start:
            time = new_task.activation
            pos = search_pos(self, time - 1)
            self.finish_events = copy.deepcopy(self.finish_events_list[pos])
            self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
            self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
            self.start_events = copy.deepcopy(self.start_events_list[pos])
            self.executing = copy.deepcopy(self.executing_list[pos])
            self.tasks.append(new_task)
            new_task.init = new_task.activation
            event = SchedEvent.ScheduleEvent(new_task.activation, new_task, SchedEvent.EventType.activation.value, self.event_id)
            self.event_id += 1
            for p in range(pos + 1):
                self.arrival_events_list[p].append(copy.deepcopy(event))
                self.arrival_events_list[p].sort(key=lambda x: x.timestamp)
            self.arrival_events.append(copy.deepcopy(event))
            self.arrival_events.sort(key=lambda x: x.timestamp)
            time = self.time_list[pos] + 1
            delete(self, time)
        else:
            reset(self)
            self.tasks.append(new_task)
            self.arrival_events = self.get_all_arrivals()
            count = self.size - 1
        self.output_file.clean(time)
        self.compute(time, count)

    def add_time(self, add_time):
        self.add_arrivals(self.end, self.end + add_time)
        pos = search_pos(self, self.end - 1)
        self.finish_events = copy.deepcopy(self.finish_events_list[pos])
        self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
        self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
        self.start_events = copy.deepcopy(self.start_events_list[pos])
        self.executing = copy.deepcopy(self.executing_list[pos])
        self.end += add_time
        time = self.time_list[pos] + 1
        delete(self, time)
        self.output_file.clean(time)
        self.compute(time, self.start)

    def terminate(self):
        self.output_file.terminate_write()


class HRRN(NonPreemptive):

    def __init__(self, output_file):
        super().__init__(output_file)
        self.name = 'HRRN'

    def compute(self, time, count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            self.calculate_responsive_ratio(time)
            # Sort by response ratio:
            self.start_events.sort(key=lambda x: x.response_ratio, reverse=True)
            self.find_start_events(time)

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                count = 0
            time += 1

    def execute(self):
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        count = self.size - 1
        time = self.start
        self.compute(time, count)

    def new_task(self, new_task):
        time = self.start
        count = 0
        new_task.core = self.cores[0].id
        if new_task.type == 'sporadic' and new_task.activation > self.start:
            time = new_task.activation
            pos = search_pos(self, time - 1)
            self.finish_events = copy.deepcopy(self.finish_events_list[pos])
            self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
            self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
            self.start_events = copy.deepcopy(self.start_events_list[pos])
            self.executing = copy.deepcopy(self.executing_list[pos])
            self.tasks.append(new_task)
            new_task.init = new_task.activation
            event = SchedEvent.ScheduleEvent(new_task.activation, new_task, SchedEvent.EventType.activation.value, self.event_id)
            self.event_id += 1
            for p in range(pos + 1):
                self.arrival_events_list[p].append(copy.deepcopy(event))
                self.arrival_events_list[p].sort(key=lambda x: x.timestamp)
            self.arrival_events.append(copy.deepcopy(event))
            self.arrival_events.sort(key=lambda x: x.timestamp)
            time = self.time_list[pos] + 1
            delete(self, time)
        else:
            reset(self)
            self.tasks.append(new_task)
            self.arrival_events = self.get_all_arrivals()
            count = self.size - 1
        self.output_file.clean(time)
        self.compute(time, count)

    def calculate_responsive_ratio(self, time):
        for event in self.start_events:
            if event.init <= time:
                w = time - event.init
                c = event.task.wcet
                event.response_ratio = (w + c)/c

    def add_time(self, add_time):
        self.add_arrivals(self.end, self.end + add_time)
        pos = search_pos(self, self.end - 1)
        self.finish_events = copy.deepcopy(self.finish_events_list[pos])
        self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
        self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
        self.start_events = copy.deepcopy(self.start_events_list[pos])
        self.executing = copy.deepcopy(self.executing_list[pos])
        self.end += add_time
        time = self.time_list[pos] + 1
        delete(self, time)
        self.output_file.clean(time)
        self.compute(time, self.start)

    def terminate(self):
        self.output_file.terminate_write()


class SRTF(Preemptive):

    def __init__(self, output_file):
        super().__init__(output_file)
        self.name = 'ShortestRemainingTimeFirst'

    def calculate_remaining_time(self):
        for event in self.start_events:
            event.remaining_time = event.task.wcet - event.executing_time

    def choose_executed(self, time):
        if len(self.start_events) > 0:
            self.start_events.sort(key=lambda x: x.remaining_time)
            # Non task is executed:
            if self.executing is None:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                # Create deadline event:
                self.create_deadline_event(event)
            # Change of task:
            elif self.executing.remaining_time > self.start_events[0].remaining_time and \
                    self.executing.id != self.start_events[0].id:
                # Create finish event of the current task in execution:
                finish_timestamp = time
                finish_event = SchedEvent.ScheduleEvent(
                    finish_timestamp, self.executing.task, SchedEvent.EventType.finish.value, self.executing.id)
                finish_event.job = self.executing.job
                self.output_file.add_scheduler_event(finish_event)
                # Change task:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                # Create deadline event:
                if event.task.first_time_executing:
                    self.create_deadline_event(event)

    def compute(self, time, count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            self.calculate_remaining_time()
            self.choose_executed(time)
            if self.executing:
                self.executing.executing_time += 1

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                count = 0
            time += 1

    def execute(self):
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        count = self.size - 1
        time = self.start
        self.compute(time, count)

    def new_task(self, new_task):
        time = self.start
        count = 0
        new_task.core = self.cores[0].id
        if new_task.type == 'sporadic' and new_task.activation > self.start:
            time = new_task.activation
            pos = search_pos(self, time - 1)
            self.finish_events = copy.deepcopy(self.finish_events_list[pos])
            self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
            self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
            self.start_events = copy.deepcopy(self.start_events_list[pos])
            self.executing = copy.deepcopy(self.executing_list[pos])
            if self.executing:
                self.executing = self.start_events[0]
            self.tasks.append(new_task)
            new_task.init = new_task.activation
            event = SchedEvent.ScheduleEvent(new_task.activation, new_task, SchedEvent.EventType.activation.value, self.event_id)
            self.event_id += 1
            for p in range(pos + 1):
                self.arrival_events_list[p].append(copy.deepcopy(event))
                self.arrival_events_list[p].sort(key=lambda x: x.timestamp)
            self.arrival_events.append(copy.deepcopy(event))
            self.arrival_events.sort(key=lambda x: x.timestamp)
            time = self.time_list[pos] + 1
            delete(self, time)
        else:
            reset(self)
            self.tasks.append(new_task)
            self.arrival_events = self.get_all_arrivals()
            count = self.size - 1
        self.output_file.clean(time)
        self.compute(time, count)

    def add_time(self, add_time):
        self.add_arrivals(self.end, self.end + add_time)
        pos = search_pos(self, self.end - 1)
        self.finish_events = copy.deepcopy(self.finish_events_list[pos])
        self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
        self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
        self.start_events = copy.deepcopy(self.start_events_list[pos])
        self.executing = copy.deepcopy(self.executing_list[pos])
        if self.executing:
            self.executing = self.start_events[0]
        self.end += add_time
        time = self.time_list[pos] + 1
        delete(self, time)
        self.output_file.clean(time)
        self.compute(time, self.start)

    def terminate(self):
        self.output_file.terminate_write()


class RoundRobin(Preemptive):

    def __init__(self, output_file, quantum):
        super().__init__(output_file)
        self.name = 'RoundRobin'
        self.quantum = int(quantum)
        self.quantum_counter = 0

    def choose_executed(self, time):
        if len(self.start_events) > 0:
            # Non task is executed:
            if self.executing is None:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                # Create deadline event:
                self.create_deadline_event(event)
                # Restart quantum counter
                self.quantum_counter = 0
            # Change of task:
            elif self.quantum_counter == self.quantum:
                # Create finish event of the current task in execution:
                finish_timestamp = time
                finish_event = SchedEvent.ScheduleEvent(
                    finish_timestamp, self.executing.task, SchedEvent.EventType.finish.value, self.executing.id)
                finish_event.job = self.executing.job
                self.output_file.add_scheduler_event(finish_event)
                # Change task:
                # 1) Delete from start_events:
                del self.start_events[0]
                # 2) Add this event to the final:
                self.start_events.append(copy.deepcopy(self.executing))
                # 3) New event:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                # Create deadline event:
                if event.task.first_time_executing:
                    self.create_deadline_event(event)
                # Restart counter
                self.quantum_counter = 0

    def compute(self, time, count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            self.choose_executed(time)
            self.quantum_counter += 1
            if self.executing:
                self.executing.executing_time += 1

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                self.quantum_counter_list.append(self.quantum_counter)
                count = 0
            time += 1

    def execute(self):
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        time = self.start
        count = self.size - 1
        self.compute(time, count)

    def new_task(self, new_task):
        time = self.start
        count = 0
        new_task.core = self.cores[0].id
        if new_task.type == 'sporadic' and new_task.activation > self.start:
            time = new_task.activation
            pos = search_pos(self, time - 1)
            self.finish_events = copy.deepcopy(self.finish_events_list[pos])
            self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
            self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
            self.start_events = copy.deepcopy(self.start_events_list[pos])
            self.executing = copy.deepcopy(self.executing_list[pos])
            self.quantum_counter = self.quantum_counter_list[pos]
            if self.executing:
                self.executing = self.start_events[0]
            self.tasks.append(new_task)
            new_task.init = new_task.activation
            event = SchedEvent.ScheduleEvent(new_task.activation, new_task, SchedEvent.EventType.activation.value, self.event_id)
            self.event_id += 1
            for p in range(pos + 1):
                self.arrival_events_list[p].append(copy.deepcopy(event))
                self.arrival_events_list[p].sort(key=lambda x: x.timestamp)
            self.arrival_events.append(copy.deepcopy(event))
            self.arrival_events.sort(key=lambda x: x.timestamp)
            time = self.time_list[pos] + 1
            delete(self, time)
        else:
            reset(self)
            self.tasks.append(new_task)
            self.arrival_events = self.get_all_arrivals()
            count = self.size - 1
        self.output_file.clean(time)
        self.compute(time, count)

    def add_time(self, add_time):
        self.add_arrivals(self.end, self.end + add_time)
        pos = search_pos(self, self.end - 1)
        self.finish_events = copy.deepcopy(self.finish_events_list[pos])
        self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
        self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
        self.start_events = copy.deepcopy(self.start_events_list[pos])
        self.executing = copy.deepcopy(self.executing_list[pos])
        self.quantum_counter = self.quantum_counter_list[pos]
        if self.executing:
            self.executing = self.start_events[0]
        self.end += add_time
        time = self.time_list[pos] + 1
        delete(self, time)
        self.output_file.clean(time)
        self.compute(time, self.start)

    def terminate(self):
        self.output_file.terminate_write()


class Critical(Scheduler):
    """
    This class represents the critical type of possible scheduling algorithms. It extends the Scheduler class
    and will be extended by all the classes that implement real-time scheduling algorithms that deal with tasks
    that can have two criticality levels.
    """

    def __init__(self, output_file):
        """
        This method initializes the Critical class extending the scheduler.
        :param output_file: The file where all the finishing events are going to be written.
        """
        super().__init__(output_file)
        self.name = 'RealTimeCriticalScheduler'

    def execute(self):
        pass

    def find_finish_events(self, time):
        """
        This method finds based on the actual time of the scheduler and timestamp of the events, the finishing events.
        Once  a finishing event is found it is directly written in the output file.
        :param time: The current time in which the scheduler is running.
        :return: No parameter is returned.
        """
        if self.executing:
            match self.mode:
                case "low":
                      if self.executing.executing_time == self.executing.task.wcet and self.executing.task.criticality=="low":
                          finish_event = SchedEvent.ScheduleEvent(time, self.executing.task, SchedEvent.EventType.finish.value, self.executing.id)
                          finish_event.job = self.executing.job
                          self.output_file.add_scheduler_event(finish_event)
                          # Delete from start_events:
                          for event in self.start_events:
                              if event.id == self.executing.id:
                                  self.start_events.remove(event)
                                  self.executing = None
                                  break
                      elif self.executing.executing_time == self.executing.task.wcet and self.executing.task.criticality=="high":
                          self.mode = "high"
                case "high":
                      if self.executing.executing_time == self.executing.task.wcet_high and self.executing.task.criticality == "high":
                          finish_event = SchedEvent.ScheduleEvent(time, self.executing.task,
                                                                  SchedEvent.EventType.finish.value, self.executing.id)
                          finish_event.job = self.executing.job
                          self.output_file.add_scheduler_event(finish_event)
                          # Delete from start_events:
                          for event in self.start_events:
                              if event.id == self.executing.id:
                                  self.start_events.remove(event)
                                  self.executing = None
                                  break

    def create_deadline_event(self, event):
        """
        This method creates a deadline event. It is the same as the one defined in the Preemptive Class.
        :param event: The event for which we want to create the deadline corresponding event.
        :return:The function does not return any parameter.
        """
        if event.task.real_time:
            deadline_timestamp = event.timestamp + event.task.deadline
            deadline_event = SchedEvent.ScheduleEvent(
                deadline_timestamp, event.task, SchedEvent.EventType.deadline.value, event.id)
            deadline_event.job = event.job
            self.deadline_events.append(deadline_event)
            event.task.first_time_executing = False
    def calculate_hyper(self):
        """
        This method calculates the hyperperiod value used in case of  Hyperperiod policy switching mode.
        :return: No value is returned from this method.
        """
        periods = []
        for task in self.tasks:
            if task.type == "periodic":
                periods.append(task.period)
        self.hyperperiod = reduce(math.lcm, periods)
        print('Hyperperiod: ' + str(self.hyperperiod))
    def switch_to_low(self,time):
        """
        This method is responsible for switching the scheduler into the low mode depending on the two possible
        policies: Hyperperiod or Idle state.
        :param time: The current time in which the scheduler is running.
        :return: No value is returned from this method.
        """
        match self.policy:
            case "Idle":
                if self.executing is None:
                    if self.mode == "high":
                        self.mode = "low"
                        print("Passing to low mode Idle policy")
            case "Hyperperiod":
                if time%self.hyperperiod==0 and self.mode=="high" and self.executing.criticality!="high":
                    self.mode = "low"
                    print("Passing to low mode hyperperiod time: " + str(time) + ",hyperperiod: " + str(self.hyperperiod))
    def add_time(self, add_time):
        self.add_arrivals(self.end, self.end + add_time)
        pos = search_pos(self, self.end - 1)
        self.finish_events = copy.deepcopy(self.finish_events_list[pos])
        self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
        self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
        self.start_events = copy.deepcopy(self.start_events_list[pos])
        self.executing = copy.deepcopy(self.executing_list[pos])
        self.quantum_counter = self.quantum_counter_list[pos]
        if self.executing:
            self.executing = self.start_events[0]
        self.end += add_time
        time = self.time_list[pos] + 1
        delete(self, time)
        self.output_file.clean(time)
        self.compute(time, self.start)

    def new_task(self, new_task):
        time = self.start
        count = 0
        new_task.core = self.cores[0].id
        if self.name == "EDF-VD":
            if new_task.criticality == "high":
                new_task.virtual_deadline = new_task.deadline * self.x
            else:
                new_task.virtual_deadline = new_task.deadline
        if new_task.type == 'sporadic' and new_task.activation > self.start:
            time = new_task.activation
            pos = search_pos(self, time - 1)
            self.finish_events = copy.deepcopy(self.finish_events_list[pos])
            self.deadline_events = copy.deepcopy(self.deadline_events_list[pos])
            self.arrival_events = copy.deepcopy(self.arrival_events_list[pos])
            self.start_events = copy.deepcopy(self.start_events_list[pos])
            self.executing = copy.deepcopy(self.executing_list[pos])
            if self.executing:
                self.executing = self.start_events[0]
            self.tasks.append(new_task)
            new_task.init = new_task.activation
            event = SchedEvent.ScheduleEvent(new_task.activation, new_task, SchedEvent.EventType.activation.value, self.event_id)
            self.event_id += 1
            for p in range(pos + 1):
                self.arrival_events_list[p].append(copy.deepcopy(event))
                self.arrival_events_list[p].sort(key=lambda x: x.timestamp)
            self.arrival_events.append(copy.deepcopy(event))
            self.arrival_events.sort(key=lambda x: x.timestamp)
            time = self.time_list[pos] + 1
            delete(self, time)
        else:
            reset(self)
            self.tasks.append(new_task)
            self.calculate_hyper()
            self.arrival_events = self.get_all_arrivals()
            count = self.size - 1
        self.output_file.clean(time)
        self.compute(time, count)
    def compute(self,time,count):
        pass

class OBCP(Critical):
    """
    The OBCP class extends the Critical class, and it implements the OBCP algorithm for real-time systems with two
    possible criticality levels low and high.
    """
    def __init__(self, output_file,policy):
        """
        This method initializes the OBCP class.
        :param output_file: The file where the finishing events are going to be written.
        :param policy: The policy that is going to be used by the OBCP algorithm to switch from high mode to low mode.
        In this implementation can take only two values: "Hypeperiod" or "Idle".
        """
        super().__init__(output_file)
        self.name = 'OBCP'
        self.policy = policy

    def choose_executed(self,time):
        """
        This method chooses the current event(task) that must be in execution. This is done based on how the events are
        sorted in the start_events list of the scheduler.
        :param time: The current time in which the scheduler is running.
        :return: No value is returned.
        """
        #Try switching on low mode based on the policy
        self.switch_to_low(time)
        print(self.mode)
        if len(self.start_events) > 0 and self.mode=="low":
            self.start_events.sort(key=lambda x: x.task.wcet)
        elif len(self.start_events) > 0 and self.mode=="high":
            self.start_events.sort(key=lambda x: x.task.criticality=="high",reverse=True)
            # Non task is executed:
        if self.executing is None and len(self.start_events)>0:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                # If the Ilde or Hyperperiod policy couldn't bring the mode to low and all the high tasks are finished
                # the scheduler passes to low mode
                if self.mode == "high" and event.task.criticality=="low":
                    self.mode = "low"
                # Create deadline event:
                self.create_deadline_event(event)

    def execute(self):
        """
        This method executes the OBCP algorithm.
        :return: No return value from this method.
        """
        if self.policy=="Hyperperiod":
            self.calculate_hyper()
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        time = self.start
        count = self.size - 1
        self.compute(time, count)

    def compute(self, time, count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            self.choose_executed(time)
            if self.executing:
                self.executing.executing_time += 1

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                count = 0
            time += 1

    def terminate(self):
        self.output_file.terminate_write()

class EDF_VD(Critical):
    """
    The EDF_VD class extends the Critical class, and it implements the EDF_VD algorithm for real-time systems with two
    possible criticality levels low and high.
    """
    def __init__(self, output_file,policy):
        """
               This method initializes the EDF_VD class.
               :param output_file: The file where the finishing events are going to be written.
               :param policy: The policy that is going to be used by the EDF_VD algorithm to switch from high mode to low mode.
               In this implementation can take only two values: "Hypeperiod" or "Idle".
        """
        super().__init__(output_file)
        self.name = 'EDF-VD'
        self.policy = policy

    def calculate(self):
        """
        The method calculates the coefficient X witch will multiply the deadline of every high criticality task.
        :return: No parameter is returned.
        """
        ul = 0
        ulh = 0
        for task in self.tasks:
            if task.criticality == "low":
                ul = ul + task.wcet/task.deadline
            if task.criticality == "high":
                ulh = ulh + task.wcet/task.deadline
        if ulh==0:
            self.x = 1
        else:
            self.x = min(1,(1-ul)/ulh)
            if self.x<=0:
                self.x = 1
        print("UL: " + str(ul))
        print("ULh" + str(ulh))

    def execute(self):
        """
        The method executes the EDF-VD algorithm.
        :return: No parameter is returned.
        """
        if self.policy=="Hyperperiod":
            self.calculate_hyper()
        self.calculate()
        print("X coeff: " + str(self.x))
        for task in self.tasks:
            if task.criticality=="high":
                task.virtual_deadline = task.deadline * self.x
            else:
                task.virtual_deadline = task.deadline
            print(str(task.id) + ": " + str(task.virtual_deadline))
        self.arrival_events = self.get_all_arrivals()
        self.size = int(math.sqrt(self.end - self.start))
        time = self.start
        count = self.size - 1
        self.compute(time, count)

    def compute(self,time,count):
        while time <= self.end:
            self.find_finish_events(time)
            self.find_deadline_events(time)
            self.find_arrival_event(time)
            self.choose_executed(time)
            if self.executing:
                self.executing.executing_time += 1

            count += 1
            if count == self.size:
                self.time_list.append(time)
                self.finish_events_list.append(copy.deepcopy(self.finish_events))
                self.deadline_events_list.append(copy.deepcopy(self.deadline_events))
                self.arrival_events_list.append(copy.deepcopy(self.arrival_events))
                self.start_events_list.append(copy.deepcopy(self.start_events))
                self.executing_list.append(copy.deepcopy(self.executing))
                count = 0
            time += 1

    def choose_executed(self,time):
        """
                This method chooses the current event(task) that must be in execution. This is done based on how the events are
                sorted in the start_events list of the scheduler.
                :param time: The current time in which the scheduler is running.
                :return: No value is returned.
        """
        self.switch_to_low(time)
        print(self.mode)
        if len(self.start_events) > 0 and self.mode=="low":
            self.start_events.sort(key=lambda x: x.task.virtual_deadline - time)
        elif len(self.start_events) > 0 and self.mode=="high":
            self.start_events.sort(key=lambda x: (x.task.criticality=="low",x.task.deadline - time))

        #Try switching the current running task with one in a higher priority
        if self.executing and self.mode=="low":
            self.try_to_switch(time)

        # Non task is executed:
        elif self.executing is None and len(self.start_events)>0:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                #Switch to low mode if high tasks are finished
                if event.task.criticality=="low" and self.mode=="high":
                    self.mode = "low"
                # Create deadline event:
                self.create_deadline_event(event)

    def try_to_switch(self,time):
        """
        The method switches the current event executing with one of a higher priority.
        :param time: The current time in whitch the scheduler is running.
        :return: No parameter is returned
        """
        if self.executing.task.criticality == "low":
            if self.executing.task.virtual_deadline - time > self.start_events[0].task.virtual_deadline - time and self.executing.id!=self.start_events[0].id:
                finish_timestamp = time
                finish_event = SchedEvent.ScheduleEvent(
                    finish_timestamp, self.executing.task, SchedEvent.EventType.finish.value, self.executing.id)
                finish_event.job = self.executing.job
                self.output_file.add_scheduler_event(finish_event)
                # Change task:
                event = self.start_events[0]
                event.timestamp = time
                self.output_file.add_scheduler_event(event)
                self.executing = event
                print("Switching task; time = " + str(time))
                # Create deadline event:
                if event.task.first_time_executing:
                    self.create_deadline_event(event)




    def terminate(self):
        self.output_file.terminate_write()