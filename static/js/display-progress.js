$(document).ready(function() {
    var domain = $("#domain").text();
    var status = $("#status").text();
    switch (status) {
        case 'created':
            // console.log('here we go!');
            // start_external_spider
            $.post("/api/start_external_crawl/", { domain: domain })
            .done(function(data1) {
                console.log('data1:')
                console.log(data1)
            })
            .fail(function(data2) {
                console.log('data2:')
                console.log(data2)
                alert("error occured while starting external scan");
            });
            // get job_id [optional kill job]
            // get status of job
            break;
        case 'external_started':
            $.post("/api/domain_job_status/", { domain: domain, spider: 'external' })
            .done(function(data4) {
                console.log('data4:')
                console.log(data4)
            })
            .fail(function(data5) {
                console.log('data5:')
                console.log(data5)
                alert("error occured while asking job status");
            });
            break;
        case 'external_finished':
            break;
        case 'info_started':
            // wait info finish
            break;
        case 'info_finished':
            // wait info finish
            break;
        case 'finished':
            // wait info finish
        default:
            // reload_page()
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