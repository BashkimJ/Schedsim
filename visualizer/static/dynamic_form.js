$(document).ready(function() {
    let taskCount = 0;

    $('#newTaskBtn').click(function() {
        $('#newTaskForm').removeClass('hidden');
        $('#createXML').addClass('hidden');
        $('#printGraphForm').addClass('hidden');
        $('.graph-execution').addClass('hidden');
        $('#addTimeForm').addClass('hidden');
    });

    function toggleFields(taskCount) {
        var taskType = $(`#taskType_${taskCount}`).val();
        var periodGroup = $(`#periodGroup_${taskCount}`);
        var activationGroup = $(`#activationGroup_${taskCount}`);

        if (taskType === "periodic") {
            periodGroup.removeClass("hidden");
            activationGroup.addClass("hidden");
        } else if (taskType === "sporadic") {
            periodGroup.addClass("hidden");
            activationGroup.removeClass("hidden");
        } else {
            periodGroup.addClass("hidden");
            activationGroup.addClass("hidden");
        }

        console.log("Period Group hidden:", periodGroup.hasClass('hidden'));
        console.log("Activation Group hidden:", activationGroup.hasClass('hidden'));
    }

    $('#createXMLBtn').click(function() {
        $('#createXML').removeClass('hidden');
        $('#newTaskForm').addClass('hidden');
        $('#printGraphForm').addClass('hidden');
        $('.graph-execution').addClass('hidden');
        $('#addTimeForm').addClass('hidden');
    });

    $('#addTaskBtn').click(function() {
        taskCount++;
        const formId = `dynamicTaskForm_${taskCount}`;
        const dynamicFormHtml = `
            <form id="${formId}" class="styled-form">
                <h3>TASK_${taskCount}</h3>
                <div class="form-group">
                    <label for="realTime_${taskCount}">Real Time (true/false)</label>
                    <select id="realTime_${taskCount}" name="realTime_${taskCount}" required>
                        <option value="True">True</option>
                        <option value="False">False</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="taskType_${taskCount}">Task Type (sporadic/periodic)</label>
                    <select id="taskType_${taskCount}" name="taskType_${taskCount}" required>
                        <option value="sporadic">sporadic</option>
                        <option value="periodic">periodic</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="taskId_${taskCount}">Task ID</label>
                    <input type="number" id="taskId_${taskCount}" name="taskId_${taskCount}" min="1" step="1" required>
                </div>

                <div class=" hidden" id="periodGroup_${taskCount}">
                    <div class="form-group" >
                        <label for="period_${taskCount}">Period</label>
                        <input type="number" id="period_${taskCount}" name="period_${taskCount}">
                    </div>
                    
                </div>
                

                <div class=" hidden" id="activationGroup_${taskCount}">
                    <div class="form-group ">
                        <label for="activation_${taskCount}">Activation</label>
                        <input type="number" id="activation_${taskCount}" name="activation_${taskCount}">
                    </div> 
                </div>

                <div class="form-group">
                    <label for="deadline_${taskCount}">Deadline</label>
                    <input type="number" id="deadline_${taskCount}" name="deadline_${taskCount}" required>
                </div>

                <div class="form-group">
                    <label for="wcet_${taskCount}">WCET</label>
                    <input type="number" id="wcet_${taskCount}" name="wcet_${taskCount}" required>
                </div>
                <div class="form-group">
                    <label for = "wcet_high_${taskCount}">WCET_HIGH</label>
                    <input type="number" id="wcet_high_${taskCount}" name="wcet_high_${taskCount}" required>
                </div>
                <div class="form-group">
                    <label for = "criticcality_${taskCount}">Criticality</label>
                    <select id="criticality_${taskCount}" name="criticality_${taskCount}">
                        <option value="high">High-Criticality</option>
                        <option value="low">Low-Criticality</option>
                    </select>
                </div>
            </form>
        `;
        $('#dynamicTaskForm').append(dynamicFormHtml);

        $(`#taskType_${taskCount}`).change(function() {
            toggleFields(taskCount);
        });

        toggleFields(taskCount);
    });

    $('#submitAllTasksBtn').click(function() {
        const allTasksData = [];
        const start = parseInt($('#start').val());
        const end = parseInt($('#end').val());
        const schedulingAlgorithm = $('#schedulingAlgorithm').val();
        let quantum = parseInt($('#quantum').val());
        if (isNaN(quantum)) {
            quantum = 0;
        }
        if (isNaN(start) || isNaN(end) || start >= end || start < 0 || end <= 0) {
            alert('Start time must be less than end time and greater than 0.');
            return;
        }

        if (schedulingAlgorithm === 'RR' && quantum <= 0) {
            alert('Quantum must be greater than 0.');
            return;
        }

        allTasksData.push(start);
        allTasksData.push(end);
        allTasksData.push(schedulingAlgorithm);
        allTasksData.push(quantum);

        for (let i = 1; i <= taskCount; i++) {
            const realTime = $(`#realTime_${i}`).val();
            const taskType = $(`#taskType_${i}`).val();
            const taskId = parseInt($(`#taskId_${i}`).val());
            const period = parseInt($(`#period_${i}`).val()) || 0;
            const activation = parseInt($(`#activation_${i}`).val()) || 0;
            const deadline = parseInt($(`#deadline_${i}`).val());
            const wcet = parseInt($(`#wcet_${i}`).val());
            const wcet_high = parseInt($(`#wcet_high_${i}`).val());
            const criticality = $('#criticality_${i}').val();

            if (taskId <= 0 || wcet <= 0 || deadline <= 0) {
                alert(`Invalid inputs for task ${i}.`);
                return;
            }

            if ((taskType === 'periodic' && (period <= 0 || period >= deadline || wcet > period)) ||
                (taskType === 'sporadic' && activation < 0) ||
                (deadline < wcet) || (deadline<wcet_high) || (wcet_high<=wcet)) {
                alert(`Invalid scheduling parameters for task ${i}.`);
                return;
            }

            allTasksData.push(parseBool(realTime));
            allTasksData.push(taskType);
            allTasksData.push(taskId);
            allTasksData.push(period);
            allTasksData.push(activation);
            allTasksData.push(deadline);
            allTasksData.push(wcet);
            allTasksData.push(wcet_high);
            allTasksData.push(criticality);
        }

        $.ajax({
            url: '/submit_all_tasks',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(allTasksData),
            success: function(response) {
                alert('All tasks submitted successfully!');
                $('#newTaskForm').addClass('hidden');
                $('#createXML').addClass('hidden');
                $('#printGraphForm').addClass('hidden');
                $('.graph-execution').addClass('hidden');
                $('#addTimeForm').addClass('hidden');
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error
                    ? xhr.responseJSON.error
                    : 'Error occurred while submitting tasks.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
    });

    function parseBool(value) {
        return value.toLowerCase() === 'true';
    }
});
