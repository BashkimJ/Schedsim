# SchedSim
SchedSim is a collection of tools to test task scheduling algorithm (both real-time and non real-time).
The software is currently under development by [HEAPLab](https://heaplab.deib.polimi.it) students and researchers.

## Contributors on this branch
- Bashkim Jance

## Execute
<p align="center">
  <img src="./docs/schedsim_base.PNG" />
</p>
Move in the `visualizer` folder and run `python3 ConnectionHandler.py` to open the web application.

There you have different buttons:
- `Start`: starts the execution of the scheduling algorithm.
- `New Task`: add a new task in the current execution.
- `Add Time`: add a selected amount of time in the current execution.
- `Print Graph`: print a diagram of the current execution with the different executing tasks in the various time instances. You can also insert the time interval where you want to see the task execution 
- `Select and Upload XML File`: Select an XML file from your pc to be executed.
- `Create XML`: You can create an XML file by choosing the starting configuration and the tasks that you want with the command `Add New Task`. The file will be saved in the `visualizer/Input` folder.
- `Download CSV`: save the result in a csv format.
- `Download XML` : save the created XML file.

## Documentation
Detailed documentation on how to use the simulator and the available features can be found in the [docs](./docs/Schedsim_documentation.pdf) directory.

## License
SchedSim is Open Source and released under the Apache license. See the [LICENSE](./LICENSE) file for further details.
