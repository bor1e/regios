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
        $.get("/api/cancel_job/" + job_id, {}, function(data) {
            $('#job_status_' + spider).html('canceled while in state: ' + data.state);
            $('#process').html('canceled after running for');
        });
        // alert( "Handler for .click() called with job_id: " + job_id );
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
                        //   location.reload();
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
            getStatusOfSpiderForDomain('info');
            break;
        default:
            //location.reload();
            break;
    }

    //return startScraping('botspider', domain, url, '#status', 'None');
});

function startScraping(spider, domain, url, display_id, job) {
    var start_spider = {
        domain: domain,
        url: url,
        name: spider,
        keywords: $("#domain").text(),
        display_id: display_id,
        job: job
    }
    //simple spider checking only Impressum, Title, Keywords
    $.post("/api/post/", start_spider,
        function(data) {
            console.log(data);
            if (data.info) {
                console.log('info received for: ' + start_spider.domain)
                $(start_spider.display_id).html('data exists in DB');
                return;
            }
            console.log('starting spider for: ' + start_spider.domain)
            var interval = 1500;
            (function doUpdate() {
                $.get("/api/get/", { task_id: data['task_id'], domain: start_spider.domain },
                        function(new_data) {
                            if (new_data.status)
                                $(start_spider.display_id).html('<div class="control is-loading">' +
                                    '<input class="input" type="text" value="' + new_data.status +
                                    '" readonly></div>');
                            else {
                                console.log(new_data);
                                $(start_spider.display_id).html(new_data.data.status);
                            }
                        })
                    .done(function() {
                        var status = $(start_spider.display_id).text()
                        if (status == 'finished' && start_spider.job == 'None') {
                            console.log(start_spider.display_id)
                            location.reload(true);
                        } else if (status == 'finished' && start_spider.job == 'refresh') {
                            console.log('finished domain: ' + start_spider.domain);
                            location.reload(true);
                        } else {
                            console.log('not finished... ');
                            setTimeout(doUpdate, interval);
                        }
                    });
            })();
        });
}