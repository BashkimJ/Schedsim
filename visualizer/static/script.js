document.addEventListener('DOMContentLoaded', function() {
    let uploadedFilePath = '';
    $('.graph-execution').addClass('hidden');

    // Function to manage dinamically the PERIODIC/SPORADIC tasks
    function toggleFields() {
        var taskType = $('#taskType').val();
        var periodGroup = $('#periodGroup');
        var activationGroup = $('#activationGroup');
    
        if (taskType === "periodic") {
            console.log("Showing Period");
            periodGroup.removeClass("hidden");
            activationGroup.addClass("hidden");
        } else if (taskType === "sporadic") {
            console.log("Showing Activation");
            periodGroup.addClass("hidden");
            activationGroup.removeClass("hidden");
        } else {
            console.log("Hiding Both");
            periodGroup.addClass("hidden");
            activationGroup.addClass("hidden");
        }

    }
    $('#taskType').change(toggleFields);
    toggleFields();

    // Function to manage dinamically the QUANTUM for RR algorithm
    function toggleFieldsQuantum() {
        var schedulingAlgorithm = $('#schedulingAlgorithm').val();
        var quantumGroup = $('#quantumGroup');
        var policyGroup = $('#policy');

        if (schedulingAlgorithm === "RR") {
            console.log("Showing Quantum");
            quantumGroup.removeClass("hidden");
        }
        else if(schedulingAlgorithm === "EDF-VD" || schedulingAlgorithm==="OBCP"){
            policyGroup.removeClass("hidden")
        }
         else {
            console.log("Hiding Quantum");
            quantumGroup.addClass("hidden");
            policyGroup.addClass("hidden")
        }
    }
    $('#schedulingAlgorithm').change(toggleFieldsQuantum);
    toggleFieldsQuantum();

    $('#newTaskBtn').click(function() {
        $('#newTaskForm')[0].reset(); 
        $('#newTaskForm').removeClass('hidden');
        $('#createXML').addClass('hidden');
        $('#printGraphForm').addClass('hidden');
        $('.graph-execution .large-image').addClass('hidden');
        $('#addTimeForm').addClass('hidden');
    });

    $('#createXMLBtn').click(function() {
        $('#createXML')[0].reset(); 
        $('#createXML').removeClass('hidden');
        $('#newTaskForm').addClass('hidden');
        $('#printGraphForm').addClass('hidden');
        $('.graph-execution .large-image').addClass('hidden');
        $('#addTimeForm').addClass('hidden');
    });

    $('#newTaskForm').submit(function(event) {
        event.preventDefault();
    
        const formData = new FormData(this);

        $.ajax({
            url: '/create_task',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                alert(response.message || 'Task created successfully!');
                $('#newTaskForm').addClass('hidden');
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while creating task.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
    });

    $('#createXML').submit(function(event) {
        event.preventDefault();
        $('#createXML').removeClass('hidden');
    });
    
    $('#xmlFile').change(function() {
        if (this.files.length > 0) {
            $('.graph-execution').addClass('hidden');
            $('.graph-execution .large-image').addClass('hidden');
            $('#printGraphForm').addClass('hidden');
            // Automatic submit of the form
            $('#xmlForm').submit();
        }
    });

    $('#xmlForm').submit(function(event) {
        event.preventDefault();
        
        const formData = new FormData(this);

        $.ajax({
            url: '/upload_xml',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                alert('XML File uploaded successfully!');
                uploadedFilePath = response.file_path;
                $('.graph-execution').addClass('hidden');
                $('.graph-execution .large-image').addClass('hidden');
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while uploading XML file.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
    });

    $('#executeBtn').click(function() {
        $('#newTaskForm').addClass('hidden');
        $('#createXML').addClass('hidden');
        $('#printGraphForm').addClass('hidden');
        $('.graph-execution .large-image').addClass('hidden');
        $('#addTimeForm').addClass('hidden');

        if (uploadedFilePath === '') {
            alert('Please upload an XML file first.');
            return;
        }

        $.ajax({
            url: '/execute_main',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ file_path: uploadedFilePath }),
            success: function(response) {
                alert(response.output || 'Execution completed successfully!');
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while executing command.';
                console.error('XHR Status:', xhr.status);
                console.error('Error:', xhr.statusText);
                console.error('Response Text:', xhr.responseText);
                alert(errorMessage);
            }
        });
    });

    $('#addTimeBtn').click(function() {
        $('#addTimeForm')[0].reset(); // Reset the form
        $('#newTaskForm').addClass('hidden');
        $('#createXML').addClass('hidden');
        $('#printGraphForm').addClass('hidden');
        $('.graph-execution .large-image').addClass('hidden');
        $('#addTimeForm').removeClass('hidden');
        $('.graph-execution').addClass('hidden');
    });

    $('#addTimeForm').submit(function(event) {
        event.preventDefault();
        let n_time = $('#newTime').val();
        
        if (n_time) {
            $.ajax({
                url: '/add_time',
                type: 'POST',
                data: JSON.stringify({ new_time: parseInt(n_time) }),
                contentType: 'application/json',
                success: function(response) {
                    alert(response.message);
                    $('#addTimeForm').addClass('hidden');
                },
                error: function(xhr, status, error) {
                    alert("Error: " + xhr.responseJSON.error);
                }
            });
        }
    });

    $('#printGraphBtn').click(function() {
        $('#printGraphForm')[0].reset(); 

        const fixedParams = {
            use_fixed_params: true
        };
        
        $.ajax({
            url: '/print_graph',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(fixedParams),
            success: function(response) {
                alert(response.message || 'Graph printed successfully!');
                $('.graph-execution').removeClass('hidden');
                $('.graph-execution .large-image').removeClass('hidden');
                // Refresh the image source to prevent caching issues
                $('.graph-execution .large-image').attr('src', '/static/out.png?' + new Date().getTime());
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while printing graph.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
        
        $('#printGraphForm').removeClass('hidden');
        $('#newTaskForm').addClass('hidden');
        $('#createXML').addClass('hidden');
        $('#addTimeForm').addClass('hidden');
    });
    
    $('#printGraphForm').submit(function(event) {
        event.preventDefault();
    
        const startTime = $('#start_time').val();
        const endTime = $('#end_time').val();
        const fracTime = $('#frac_time').val();
    
        if (startTime === '' || endTime === '' || fracTime === '') {
            alert('Please fill in all parameters.');
            return;
        }
    
        const formData = {
            start_time: parseInt(startTime),
            end_time: parseInt(endTime),
            frac_time: parseInt(fracTime)
        };
    
        $.ajax({
            url: '/print_graph',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                alert(response.message || 'Graph printed successfully!');
                // Show the .graph-execution element and the graph image
                $('.graph-execution').removeClass('hidden');
                $('.graph-execution .large-image').removeClass('hidden');
                // Refresh the image source to prevent caching issues
                $('.graph-execution .large-image').attr('src', '/static/out.png?' + new Date().getTime());
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while printing graph.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
    });

    $('#downloadCsvBtn').click(function() {
        $.ajax({
            url: '/download_csv',
            type: 'GET',
            success: function(response) {
                // Create a temporany URL to download the CSV file
                const url = window.URL.createObjectURL(new Blob([response]));
                const a = document.createElement('a');
                a.href = url;
                a.download = 'data.csv';
                document.body.appendChild(a);
                a.click();
                // Release the memory after the operation
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url); 
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while downloading CSV file.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
    });
    
    $('#downloadXmlBtn').click(function() {
        $.ajax({
            url: '/download_xml',
            type: 'GET',
            success: function(response) {
                // Create a temporany URL to download the XML file
                const url = window.URL.createObjectURL(new Blob([response]));
                const a = document.createElement('a');
                a.href = url;
                a.download = 'data.xml'; 
                document.body.appendChild(a);
                a.click();
                // Release the memory after the operation
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url); 
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                                    ? xhr.responseJSON.error 
                                    : 'Error occurred while downloading XML file.';
                console.error(errorMessage);
                alert(errorMessage);
            }
        });
    });

});
