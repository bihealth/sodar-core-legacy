// Project list filtering
$(document).ready(function () {
    $('#sodar-pr-home-display-notfound').hide();
    $('#sodar-pr-home-display-nostars').hide();

    // Filter input
    $('#sodar-pr-project-list-filter').keyup(function () {
        var v = $(this).val().toLowerCase();
        var valFound = false;
        $('#sodar-pr-home-display-nostars').hide();

        if (v.length > 2) {
            $('.sodar-pr-home-display-default').hide();
            $('#sodar-pr-project-list-filter').removeClass('text-danger').addClass('text-success');
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');

            $('.sodar-pr-project-list-item').each(function () {
                var fullTitle = $(this).attr('data-full-title');
                var titleLink = $(this).find('td:first-child div span.sodar-pr-project-title a');

                if (titleLink && fullTitle.toLowerCase().indexOf(v) !== -1) {
                    $(this).find('.sodar-pr-project-indent').hide();
                    // Reset content for updating the highlight
                    titleLink.html(fullTitle);
                    // Highlight
                    var pattern = new RegExp("(" + v + ")", "gi");
                    var titlePos = fullTitle.toLowerCase().indexOf(v);
                    if (titlePos !== -1) {
                        var titleVal = fullTitle.substring(titlePos, titlePos + v.length);
                        titleLink.html(fullTitle.replace(
                            pattern, '<span class="sodar-search-highlight">' + titleVal + '</span>'));
                    }
                    $(this).show();
                    valFound = true;
                    $('#sodar-pr-home-display-notfound').hide();
                } else {
                    $(this).hide();
                }
            });
            if (valFound === false) {
                $('#sodar-pr-home-display-notfound').show();
            }
        } else {
            $('.sodar-pr-project-list-item').each(function () {
                var anchor = $(this).find('a.sodar-pr-project-link');
                var title = $(this).attr('data-title');
                if (anchor) anchor.text(title);
                else $(this).find('span.sodar-pr-project-title').text(title);
                $(this).show();
                $(this).find('.sodar-pr-project-indent').show();
            });
            $('#sodar-pr-home-display-notfound').hide();
            $('#sodar-pr-project-list-filter').addClass(
                'text-danger').removeClass('text-success');
            $('#sodar-pr-project-list-link-star').attr('data-filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });

    // Filter by starred
    $('#sodar-pr-project-list-link-star').click(function () {
        $('#sodar-pr-home-display-notfound').hide();
        $('#sodar-pr-project-list-filter').val('');

        if ($(this).attr('data-filter-mode') === '0') {
            var starCount = 0;
            $('.sodar-pr-project-list-item').each(function () {
                if ($(this).attr('data-starred') === '1') {
                  $(this).find('.sodar-pr-project-indent').hide();
                  $(this).find('a.sodar-pr-project-link').text($(this).attr('data-full-title'));
                  $(this).show();
                  starCount += 1;
                } else $(this).hide();
            });
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star"></i> Starred');
            $(this).attr('data-filter-mode', '1');
            if (starCount === 0) {
                $('#sodar-pr-home-display-nostars').show();
            }
        } else if ($(this).attr('data-filter-mode') === '1') {
            $('#sodar-pr-home-display-nostars').hide();
            $('.sodar-pr-project-list-item').each(function () {
                $(this).find('.sodar-pr-project-indent').show();
                $(this).find('a.sodar-pr-project-link').text($(this).attr('data-title'));
                $(this).show();
            });
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');
            $(this).attr('data-filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });
});

// Retrieve custom column data
$(document).ready(function () {
    // Grab column app names and IDs from header into a list
    var colIds = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        colIds.push({
            app: $(this).attr('data-app-name'),
            id: $(this).attr('data-column-id')
        });
    });
    if (colIds.length === 0) return; // Skip if no columns were found

    // Get UUIDs (skip categories)
    var projectUuids = [];
    $('.sodar-pr-project-list-item-project').each(function () {
        projectUuids.push($(this).attr('data-uuid'));
    });
    if (projectUuids.length === 0) return; // Skip if there are no projects

    // Retrieve column data
    $.ajax({
        url: $('.sodar-pr-project-list-header').attr('data-custom-col-url'),
        method: 'POST',
        dataType: 'json',
        contentType : 'application/json',
        data: JSON.stringify({'projects': projectUuids})
    }).done(function (data) {
        // Update columns
        $('.sodar-pr-project-list-item-project').each(function () {
            var projectData = data[$(this).attr('data-uuid')];
            var i = 0;
            $(this).find('.sodar-pr-project-list-custom').each(function () {
                $(this).html(projectData[colIds[i].app][colIds[i].id].html);
                i += 1;
            });
        });
    });
});
