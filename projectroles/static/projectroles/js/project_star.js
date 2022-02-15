/* Star/unstar project ------------------------------------------------------ */

$(document).ready(function () {
    $('#sodar-pr-link-project-star').click(function () {
        $.post({
            url: $(this).attr('star-url'),
            method: 'POST',
            dataType: 'json'
        }).done(function (data) {
            if (data === 1) {
                $('#sodar-pr-link-project-star').html(
                    '<i class="iconify text-warning" ' +
                    'data-icon="mdi:star" data-height="30"></i>'
                ).attr('data-original-title', 'Unstar');
            } else {
                $('#sodar-pr-link-project-star').html(
                    '<i class="iconify text-muted" ' +
                    'data-icon="mdi:star-outline" data-height="30"></i>'
                ).attr('data-original-title', 'Star');
            }
        }).fail(function () {
            alert('Error: unable to set project star!');
        });
    });
});
