var canceled = false;

function getStatusOfSpiderForDomain(domain, spider) {
    $.get("/api/scrapyd/", function(data) {
            console.log('Scrapy running properly');
            if (data.data.status != 'ok')
                alert('Problem with Scrapyd. Please check that everything is running properly.');
        })
        .fail(function() {
            alert('Problem with Scrapyd. Please check that everything is running properly.');
        });
    (function getStatus() {
        $.post("/api/domain_spider_status/", { domain: domain, spider: spider })
            .done(function(data) {
                // console.log(data);
                // console.log(canceled);
                if (data.status != 'finished') {
                    if (data.status == 'pending') {
                        $("#cancel_job").hide();
                    } else if (!canceled) {
                        $("#cancel_job").show();
                        $('#status').html(spider + 'spider is ' + data.status);
                        $('#remaining_infoscan').html(data.remaining_info);
                    }
                    setTimeout(getStatus, 2000);
                } else {
                    if (canceled) {
                        if (spider == 'info') 
                            canceled = false;
                    }
                    $('#status').html(spider + 'spider is ' + data.status);
                    $('#remaining_infoscan').html(data.remaining_info);
                    location.reload();
                }
            })
            .fail(function(error) {
                alert("error occured while checking job status");
            });
    })();
}

var domain = $("#domain").text();
var status = $("#status").text();
if (status == 'external_started' || status == 'refreshing') {
    getStatusOfSpiderForDomain(domain, 'external');
} else if (status == 'info_started') {
    getStatusOfSpiderForDomain(domain, 'info');
}

$("#cancel_job").click(function() {
    var job_id = $(this).val();
    console.log('job_id: '+job_id)
    var spider = (($(this).text() == 'Cancel Infospider') ? 'infospider' : 'externalspider');
    $.get("/api/cancel_job/" + job_id, { domain: domain, spider: spider }, function(data) {
        $("#status").html(spider + ' canceled, waiting spider to close.');
        //var msg = "since the crawling was canceled, page is being reloaded.";
        //setTimeout(location.reload(), 20000);
    });
    canceled = true;
    $("#cancel_job").hide();
});

$(document).ready(function() {
    var table = $('#externals').DataTable({
        "order": [
            [5, "desc"]
        ],
        "pageLength": 100,
    });

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
    $('#externals tbody').on('click', 'tr td:nth-of-type(2), td:nth-of-type(3), td:nth-of-type(4), td:nth-of-type(5), td:nth-of-type(6)', function() {
        console.log('this clicked: ');
        console.log(this);
        $(this).find('#openEdit').removeAttr("hidden");
        $(this).find('#displayEditable').hide();

        $(this).find('#edit').removeAttr("disabled");
        $(this).parent().find('#submitButton').removeAttr("hidden");

    });
    $('.table tbody').on('click', 'tr td:nth-of-type(1), td:nth-of-type(2), td:nth-of-type(3), td:nth-of-type(4), td:nth-of-type(5)', function() {
        console.log('this clicked: ');
        console.log(this);
        $(this).find('#openEdit').removeAttr("hidden");
        $(this).find('#displayEditable').hide();

        $(this).find('#edit').removeAttr("disabled");
        $(this).parent().find('#submitButton').removeAttr("hidden");

    });
    document.onkeydown = function(evt) {
        evt = evt || window.event;
        var isEscape = false;
        if ("key" in evt) {
            isEscape = (evt.key === "Escape" || evt.key === "Esc");
        } else {
            isEscape = (evt.keyCode === 27);
        }
        if (isEscape) {
            console.log('received escape');
            location.reload();
        }
    };
});