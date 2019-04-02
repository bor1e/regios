$(document).ready(function() {
    var domain = $("#domain").text();
    var status = $("#status").text();
    var time = document.getElementsByTagName('time')[0],
        seconds = 0,
        minutes = 0,
        hours = 0,
        t;

    $(".button").click(function() {
        clearTimeout(t);
        var job_id = $(this).val();
        var spider = $('#spider').text().toLowerCase();
        $.get("/api/cancel_job/" + job_id, { domain: domain, spider: spider }, function(data) {
            $('#job_status_' + spider).html('canceled while in state \'' + data.state + '\'');
            $('#process').html('canceled after running for');
            $("#status").html('canceled');
            alert('since you stoped the crawling, you should go to the homepage');
            $('#cancel').remove();
        });
    });

    function add() {
        seconds++;
        if (seconds >= 60) {
            seconds = 0;
            minutes++;
            if (minutes >= 60) {
                minutes = 0;
                hours++;
            }
        }

        time.textContent = (hours ? (hours > 9 ? hours : "0" + hours) : "00") + ":" + (minutes ? (minutes > 9 ? minutes : "0" + minutes) : "00") + ":" + (seconds > 9 ? seconds : "0" + seconds);

        startTimer();
    }

    function startTimer() {
        t = setTimeout(add, 1000);
    };

    function getStatusOfSpiderForDomain(spider) {
        (function getStatus() {
            $.post("/api/domain_spider_status/", { domain: domain, spider: spider })
                .done(function(data) {
                    if (data.status != 'finished') {
                        $('#job_status_' + spider).html(data.status);
                        setTimeout(getStatus, 1000);
                    } else {
                        $('#job_status_' + spider).html(data.status);
                        location.reload();
                    }
                })
                .fail(function(error) {
                    alert("error occured while checking job status");
                });
        })();
    }
    switch (status) {
        case 'created':
            $.post("/api/start_external_crawl/", { domain: domain })
                .done(function(data) {
                    if (data.status == 'external_started') {
                        location.reload();
                    }
                })
                .fail(function(data) {
                    alert("error occured while starting external scan");
                });
            break;
        case 'external_started':
            startTimer();
            getStatusOfSpiderForDomain('external');
            break;
        case 'external_finished':
            $.post("/api/start_info_crawl/", { domain: domain })
                .done(function(data) {
                    if (data.status == 'info_started') {
                        location.reload();
                    }
                })
                .fail(function(data) {
                    alert("error occured while starting external scan");
                });
            break;
        case 'info_started':
            startTimer();
            getStatusOfSpiderForDomain('info');
            break;
        default:
            // location.reload();
            break;
    }

});