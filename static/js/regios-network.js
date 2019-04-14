$(document).ready(function() {
    var table_related = $('#related').DataTable({
        "order": [
            [5, "desc"]
        ],
        "pageLength": 50,
    });
    var table_suggested = $('#suggested').DataTable({
        "order": [
            [5, "desc"]
        ],
        "pageLength": 100,
    });
    var network = $('#network').text().trim();
    $('td.related input').change(function() {
        var path = 'change_domain_relation/' + network ;
        var msg = this.value + ' of ' + this.name + ' to/from ' + network;
        $.post(path, {domain: this.name, value: this.value}, function() {
        })
        .done(function(){
            console.log("successfully: " + msg);
        })
        .fail(function() {
            alert("failure occured while: " + msg);
        });
    });

});
