$(function () { // Ensure DOM is ready and jQuery is available
    // Toastr options configuration
    if (typeof toastr !== 'undefined') { // Check if toastr is loaded
        toastr.options = {
            "closeButton": true,
            "debug": false,
            "newestOnTop": true,
            "progressBar": true,
            "positionClass": "toast-top-right",
            "preventDuplicates": false,
            "onclick": null,
            "showDuration": "300",
            "hideDuration": "1000",
            "timeOut": "5000", // 5 seconds
            "extendedTimeOut": "1000", // 1 second
            "showEasing": "swing",
            "hideEasing": "linear",
            "showMethod": "fadeIn",
            "hideMethod": "fadeOut"
        };
    }

    // CSRF Token Setup for AJAX
    var token = $('meta[name="csrf-token"]').attr('content');
    if (token) { // Check if token exists
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", token);
                }
            }
        });
    }

    // Initialize DateTimePicker for Start Time
    var startTimePicker = $('#start_time_picker');
    if (startTimePicker.length) { // Check if the element exists
        startTimePicker.datetimepicker({
            format: 'YYYY-MM-DDTHH:mm', // Format compatible with HTML5 datetime-local
            useCurrent: false, // Important to not set time to now if field is empty or has a value
            sideBySide: true, // Show date and time pickers next to each other
            icons: { // Using Font Awesome 5 icons
                time: 'fas fa-clock',
                date: 'fas fa-calendar-alt',
                up: 'fas fa-chevron-up',
                down: 'fas fa-chevron-down',
                previous: 'fas fa-chevron-left',
                next: 'fas fa-chevron-right',
                today: 'fas fa-calendar-check',
                clear: 'fas fa-trash',
                close: 'fas fa-times'
            }
        });
    }

    // Initialize DateTimePicker for End Time
    var endTimePicker = $('#end_time_picker');
    if (endTimePicker.length) {
        endTimePicker.datetimepicker({
            format: 'YYYY-MM-DDTHH:mm',
            useCurrent: false, // Important to not set time to now if field is empty or has a value
            sideBySide: true,
            icons: {
                time: 'fas fa-clock',
                date: 'fas fa-calendar-alt',
                up: 'fas fa-chevron-up',
                down: 'fas fa-chevron-down',
                previous: 'fas fa-chevron-left',
                next: 'fas fa-chevron-right',
                today: 'fas fa-calendar-check',
                clear: 'fas fa-trash',
                close: 'fas fa-times'
            }
        });
    }

    // Optional: Link start and end time pickers (e.g., end time cannot be before start time)
    if (startTimePicker.length && endTimePicker.length) {
        startTimePicker.on("dp.change", function (e) {
            // When start_time changes, set the minimum selectable date/time for end_time_picker
            // and clear end_time_picker if it's now invalid.
            var endTimePickerInstance = endTimePicker.data("DateTimePicker");
            if (endTimePickerInstance) { // Check if instance exists
                 endTimePickerInstance.minDate(e.date);
                 // If end time was set and is now before new start time, you might want to clear it:
                 // if (endTimePickerInstance.date() && e.date && endTimePickerInstance.date().isBefore(e.date)) {
                 //    endTimePickerInstance.clear();
                 // }
            }
        });
        // Similar logic can be added for endTimePicker.on("dp.change") to restrict startTimePicker.maxDate
        // For now, just restricting end based on start.

        // Also, if end_time changes, ensure start_time is not after it
        endTimePicker.on("dp.change", function (e) {
            var startTimePickerInstance = startTimePicker.data("DateTimePicker");
            if (startTimePickerInstance) {
                startTimePickerInstance.maxDate(e.date);
                // Optional: clear start_time if it's now invalid
                // if (startTimePickerInstance.date() && e.date && startTimePickerInstance.date().isAfter(e.date)) {
                //    startTimePickerInstance.clear();
                // }
            }
        });
    }

    // AJAX for Cancel Session
    $('.btn-cancel-session').on('click', function(e) {
        e.preventDefault(); // Prevent default button action
        var $button = $(this);
        var sessionId = $button.data('session-id');
        var cancelUrl = $button.data('url');

        if (confirm('Are you sure you want to cancel this session?')) {
            $.ajax({
                url: cancelUrl,
                type: 'POST',
                // CSRF token is handled by ajaxSetup
                success: function(response) {
                    // Assuming success means the session was cancelled
                    // Update UI:
                    // 1. Change status text
                    $('#session-status-text-' + sessionId)
                        .text('Cancelled')
                        .removeClass('badge-scheduled badge-completed badge-no badge-info') // Remove other status classes
                        .addClass('badge-cancelled');

                    // 2. Disable or hide the button
                    $button.removeClass('btn-danger').addClass('btn-secondary disabled').prop('disabled', true).html('<i class="fas fa-check-circle"></i> Cancelled');

                    // Optionally, provide a more user-friendly success message than an alert.
                    // For now, an alert is fine.
                    if (response.success) {
                        // Use response.session_id from the JSON response for reliability
                        $('#session-status-text-' + response.session_id)
                            .text(response.new_status)
                            .removeClass('badge-scheduled badge-completed badge-no badge-info badge-danger')
                            .addClass('badge-' + response.new_status.toLowerCase());

                        $button.removeClass('btn-danger').addClass('btn-secondary disabled').prop('disabled', true).html('<i class="fas fa-check-circle"></i> ' + response.new_status);

                        if (toastr && response.message) {
                            toastr.success(response.message);
                        } else if (toastr) {
                            toastr.success('Session action completed.'); // Generic success
                        } else {
                            alert(response.message || 'Session action completed.');
                        }
                    } else {
                        if (toastr && response.message) {
                            toastr.error(response.message);
                        } else if (toastr) {
                            toastr.error('Failed to update session status.');
                        } else {
                            alert(response.message || 'Failed to update session status.');
                        }
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error cancelling session:", status, error, xhr.responseText);
                    var errorMessage = 'Error cancelling session. Please try again or check the console.';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    if (toastr) {
                        toastr.error(errorMessage);
                    } else {
                        alert(errorMessage);
                    }
                }
            });
        }
    });

    // AJAX for Delete Therapist
    $('.btn-delete-therapist').on('click', function(e) {
        e.preventDefault(); // Prevent default button action
        var $button = $(this);
        var therapistId = $button.data('therapist-id');
        var deleteUrl = $button.data('url');

        if (confirm('Are you sure you want to delete this therapist? This might also delete their assigned sessions.')) {
            $.ajax({
                url: deleteUrl,
                type: 'POST',
                // CSRF token is handled by ajaxSetup
                success: function(response) {
                    // Assuming success means the therapist was deleted
                    // Remove the therapist's row from the table
                    $('#therapist-row-' + therapistId).fadeOut(500, function() {
                        $(this).remove();
                        // Optional: Check if table is empty and show "No therapists found"
                        if ($('#therapist-list-table tbody tr').length === 0) {
                            // This assumes your table has id="therapist-list-table"
                            // and you have a placeholder for "No therapists found"
                            // e.g. $('#no-therapists-message').show();
                            // or refresh page: location.reload();
                        }
                    });

                    if (response.success) {
                        // Use response.therapist_id from the JSON response
                        $('#therapist-row-' + response.therapist_id).fadeOut(500, function() {
                            $(this).remove();
                            // Optional: Check if table is empty and show "No therapists found"
                        });
                        if (toastr && response.message) {
                            toastr.success(response.message);
                        } else if (toastr) {
                            toastr.success('Therapist deleted successfully.');
                        } else {
                            alert(response.message || 'Therapist deleted successfully.');
                        }
                    } else {
                        if (toastr && response.message) {
                            toastr.error(response.message);
                        } else if (toastr) {
                            toastr.error('Failed to delete therapist.');
                        } else {
                            alert(response.message || 'Failed to delete therapist.');
                        }
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error deleting therapist:", status, error, xhr.responseText);
                    var errorMessage = 'Error deleting therapist. Please try again or check the console.';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    if (toastr) {
                        toastr.error(errorMessage);
                    } else {
                        alert(errorMessage);
                    }
                }
            });
        }
    });
});
