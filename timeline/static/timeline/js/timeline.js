$(document).ready(function() {
    $('.sodar-tl-link-detail').click(function () {
        $('#sodar-modal-wait').modal('show');
        $.ajax({
            url: $(this).attr('data-url'),
            method: 'GET',
        }).done(function (data) {
            $('.modal-title').text(
                'Event Details: ' + data['app'] + '.' + data['name'] + ' (' +
                data['user'] + ' @ ' + data['timestamp'] + ')');
            $('.modal-body').html('').append($('<table>')
                .attr('class', 'table table-striped sodar-card-table')
                .attr('id', 'sodar-tl-table-detail')
                .append($('<thead>')
                    .append($('<tr>')
                        .append($('<th>').html('Timestamp'))
                        .append($('<th>').html('Description'))
                        .append($('<th>').html('Status'))
                    )
                )
                .append($('<tbody>'))
            );
            var tableBody = $('.modal-body').find('tbody');
            for (var i = 0; i < data['status'].length; i++) {
                tableBody.append($('<tr>')
                    .append($('<td>').html(data['status'][i]['timestamp']))
                    .append($('<td>').html(data['status'][i]['description']))
                    .append($('<td>')
                        .attr('class', data['status'][i]['class'])
                        .html(data['status'][i]['type'])
                    )
                );
            }
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        }).fail(function (data) {
            $('.modal-body').html('Error: ' + data);
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        });
    });
});
