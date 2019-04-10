    $.post("/api/scrapy_jobs_status/", {}, function(data) {
        if (data) {
            $('#remaining').html(data.remaining);
            $('#total_status').html(data.status);
            if (data.finished < 100)
                $('#finished_jobs').html(data.finished);
            else
                $('#finished_jobs').html('>' + data.finished);

        }
    });
    var t;

    function restart() {
        t = setTimeout(location.reload(), 10000);
    }

    $(document).ready(function() {
        var domain_array = window.location.href.split('/')
        var domain = domain_array[domain_array.length - 2]
        var url = window.location.protocol + '//' + window.location.host + '/graph/' + domain;

        var table = $('#crawling').DataTable({
            "pageLength": 100,
        });

        var $rows = table
            .rows()
            .nodes()
            .to$();
        $rows.each(function() {
            var domain = $.trim($(this).find("#domain").text());
            var job_id = $.trim($(this).find("button").val());
            var self = this;
            var payload = { domain: domain, job_id: job_id };
            $.post("/api/domain_spider_status/", payload, function(data) {
                console.log(data);
                if (data.status) {
                    console.log(domain);
                    $(self).find('.spider_status').html(data.spider + ' is ' + data.status);
                    // return;
                }
                if (data.stats) {
                    $('#remaining').html(data.stats.remaining);
                    $('#total_status').html(data.stats.status);
                    $('#finished_jobs').html(data.stats.finished);
                }
                // var job_id = $(this).find("#job_id").val();
                var spider = data.spider;
                var payload = { job_id: job_id, domain: domain, spider: spider };
                var interval = 1500;
                console.log(payload);
                (function doUpdate() {
                    $.post("/api/domain_spider_status/", payload, function(data) {
                            console.log(data);
                            if (data.status) {
                                if (data.status == 'not_found') {
                                    $(self).find('#status').html('canceled/not found');
                                    return;
                                } else {
                                    if (data.status == 'finished') {
                                        $(self).find('.spider_status').html('finished');
                                        if (spider == 'externalspider') {
                                            setTimeout(location.reload(), 10000);
                                        }
                                        return;
                                    }
                                    var msg = ''
                                    if (spider == 'infospider') {
                                        msg = ' (remaining to scan ' + data.remaining_info + ')';
                                    }
                                    $(self).find('.spider_status').html('<div class="control is-loading">' +
                                        '<input class="input" type="text" value="' + data.status + msg +
                                        '" readonly></div>');
                                }
                            }
                            if (data.stats) {
                                $('#remaining').html(data.stats.remaining);
                                $('#total_status').html(data.stats.status);
                                $('#finished_jobs').html(data.stats.finished);
                            }
                        })
                        .done(function() {

                            var status = $(self).find('.spider_status').text()
                            if (status == 'finished' || status == 'canceled/not found') {
                                console.log(domain + ' finished!')
                                //location.reload();
                                $(self).find("#cancel_job").hide();
                                clearTimeout();
                                return;
                            } else {
                                console.log(domain + ' not finished... ');
                                setTimeout(doUpdate, interval);
                            }
                        });
                })();
            });
        });
    });
    $("#cancel_job").click(function() {
        var job_id = $(this).val();
        var spider = (($(this).text() == 'Cancel Infospider') ? 'infospider' : 'externalspider');
        $.get("/api/cancel_job/" + job_id, { domain: domain, spider: spider }, function(data) {
            $("#status").html(spider + ' canceled, waiting spider to close.');
            //var msg = "since the crawling was canceled, page is being reloaded.";
            //setTimeout(location.reload(), 20000);
        });
        canceled = true;
        $("#cancel_job").hide();
    });

    function cancelJob(elem, domain) {
        var job_id = $(elem).val();
        console.log(job_id);
        $.get("/api/cancel_job/" + job_id, {}, function(data) {
            console.log(data)
            $('.' + domain).find('td').eq(1).text('cancled while in state: <b>' + data.state + '</b>');
        });
        $(elem).hide();

    }