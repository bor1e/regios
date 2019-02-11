$(document).ready(function() {
    var table = $('#externals').DataTable({
        "order": [
            [0, 'desc']
        ],
        "pageLength": 100,
    });

    // connect the checkboxes.
    // via the data table
    var $checkboxes = table
        .rows()
        .nodes()
        .to$() // Convert to a jQuery object
        .find('input[type="checkbox"].groupCheckBox');
    $("#checkAll").click(function() {
        $checkboxes.not(this).prop('checked', this.checked);
        var countCheckedCheckboxes = $checkboxes.filter(':checked').length;
        $('[id=groupCheckBox]').text(countCheckedCheckboxes);
    });
    $checkboxes.change(function() {
        var countCheckedCheckboxes = $checkboxes.filter(':checked').length;
        $('[id=groupCheckBox]').text(countCheckedCheckboxes);
    });
    $('#select_range').click(function() {
        var zip_from = parseInt($('#zip_from').val());
        var zip_to = parseInt($('#zip_to').val());
        var $rows = table
            .rows()
            .nodes()
            .to$();
        $rows.each(function() {
            var zip = parseInt($(this).find('#zip').text());
            if (zip >= zip_from && zip <= zip_to) {
                $(this).find('input[type="checkbox"].groupCheckBox').prop("checked", true);
            }
        });
        var countCheckedCheckboxes = $checkboxes.filter(':checked').length;
        $('[id=groupCheckBox]').text(countCheckedCheckboxes);
    });

    // make fields by clicking on them editable
    $('#externals tbody').on('click', 'tr td:nth-of-type(4), td:nth-of-type(5)', function() {
        $(this).find('#openEdit').removeAttr("hidden");
        $(this).find('#displayEditable').hide();

        $(this).find('#edit').removeAttr("disabled");
        $(this).find('#submitButton').removeAttr("hidden");
    });

    var isFinished = $("#status").text() == 'finished';
    var domain = $("#domain").text();
    var infoscan = false;
    if (isFinished) {
        $.post("/api/check-infoscan/", { 'domain': domain }, function(data) {
            infoscan = data.data;
            console.log('need to perform infoscan? - ' + data.data);

        }).done(function() {
            if (infoscan)
                runinfoscan(domain);
            console.log('infoscan would be run: ' + infoscan)
        });
    }

    var url = $("#url").val();
    var domain = $("#domain").text();
    return startScraping('botspider', domain, url, '#status', 'None');
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
                console.log('infe received for: ' + start_spider.domain)
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

function runinfoscan(domain) {
    $.post("/api/infoscan/", { 'domain': domain }, function(data) {
        var interval = 5000;
        console.log('data: ')
        console.log(data);
        (function doUpdate() {
            $.get("/api/scrapy_jobs_status/", { 'domain': domain, 'timer': data.time },
                    function(new_data) {
                        console.log('received new_data: ')
                        console.log(new_data);
                        if (new_data.remaining > 0)
                            $('#remaining').html('<div class="control is-loading">' +
                                '<input class="input" type="text" value="Remaining to scrap ' + new_data.remaining + ' elapsed: ' + new_data.elapsed + '" readonly></div>');
                        else {
                            $('#remaining').html(new_data.status);
                            console.log('time needed: ' + new_data.elapsed);
                        }
                    })
                .done(function() {
                    var status = $('#remaining').text();
                    if (status == 'finished') {
                        location.reload(true);
                        //setTimeout(alert('done'), interval*2);
                    } else {
                        console.log('not finished... ');
                        setTimeout(doUpdate, interval);
                    }
                });
        })();
    });
    return;
}