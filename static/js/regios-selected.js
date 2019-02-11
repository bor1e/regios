$(document).ready(function() {
    $('#externals').DataTable({
        "order": [
            [0, 'desc']
        ],
        "pageLength": 100,
    });
    var isFinished = $("#statusExternalScan").text() == 'finished';
    if (isFinished)
        return;
    $("#externals > tbody > tr").each(function() {
        var domain = $(this).find("#domain").text();
        var job_id = $(this).find("#job_id").val();
        var self = this;
        var interval = 1500;
        (function doUpdate() {
            $.get("/api/get/", { task_id: job_id, domain: domain },
                    function(data) {
                        console.log(data);
                        if (data.status) {
                            if (data.status == 'not found/canceled') {

                                $(self).find('#status').html('canceled/not found');
                            } else {
                                $(self).find('#status').html('<div class="control is-loading">' +
                                    '<input class="input" type="text" value="' + data.status +
                                    '" readonly></div>');
                            }
                        } else {
                            $(self).find('#status').html(data.data.status);
                            $(self).find('#duration').html(data.data.duration)
                        }
                    })
                .done(function() {
                    var status = $(self).find('#status').text()
                    if (status == 'finished' || status == 'canceled/not found') {
                        console.log(domain + ' finished!')
                    } else {
                        console.log('not finished... ');
                        setTimeout(doUpdate, interval);
                    }
                });
        })();
    });
    var timer = $('#timer').val();
    var interval = 3500;
    (function doUpdate() {
        $.get('/api/scrapy_jobs_status/', { timer: timer }, function(data) {
            console.log(data);
            $('#remaining').html(data.remaining);
            $('#timeElapsed').html(data.elapsed);
            $('#statusExternalScan').html(data.status);
        }).done(function() {
            if ($('#statusExternalScan').text() != 'finished') {
                setTimeout(doUpdate, interval);
            }
        });
    })();
});

function cancelJob(job_id, domain) {
    $.get("/api/cancel_job/" + job_id, {}, function(data) {
        console.log(data)
        $('.' + domain).find('td').eq(1).text('cancled while in state: <b>' + data.state + '</b>');
    });
}