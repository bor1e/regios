$(document).ready(function() {
    var domain_array = window.location.href.split('/')
    var domain = domain_array[domain_array.length-2]
    var url = window.location.protocol + '//' + window.location.host + '/graph/' + domain;
    $("a[href='/graph/FINDDOMAIN']").attr("href", url)

    var table = $('#externals').DataTable({
        "pageLength": 100,
    });
    var isFinished = $("#statusExternalScan").text() == 'finished';
    if (isFinished)
        return;

    var $rows = table
        .rows()
        .nodes()
        .to$();
    $rows.each(function() {
        var domain = $.trim($(this).find("#domain").text());
        var self = this;
        var payload = { domain: domain, name: 'externalspider', keywords: ''};
        $.post("/api/post/", payload, function(data) {
            console.log(data);
            if (data.info) {
                console.log(domain);
                $(self).find('td').eq(1).html('data exists in DB');
                return;
            }
            // var job_id = $(this).find("#job_id").val();
            $(self).find("#job_id").val(data['task_id']);

            var payload = { task_id: data['task_id'], domain: domain };
            var interval = 1500;
            (function doUpdate() {
                $.get("/api/get/", payload, function(data) {
                        console.log('received data: ' + data);
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
                            $(self).find('#externals').html(data.data.externals)
                        }
                    })
                    .done(function() {
                        var status = $(self).find('#status').text()
                        if (status == 'finished' || status == 'canceled/not found') {
                            console.log(domain + ' finished!')
                        } else {
                            console.log(domain + ' not finished... ');
                            setTimeout(doUpdate, interval);
                        }
                    });
            })();
        });
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

function cancelJob(elem, domain) {
    var job_id = $(elem).parents('tr').find('#job_id').val();
    console.log(job_id);
    $.get("/api/cancel_job/" + job_id, {}, function(data) {
        console.log(data)
        $('.' + domain).find('td').eq(1).text('cancled while in state: <b>' + data.state + '</b>');
    });
}