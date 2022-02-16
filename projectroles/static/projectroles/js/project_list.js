// Function for updating custom columns
function updateCustomColumns (uuids) {
    // Grab column app names and IDs from header into a list
    var colIds = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        colIds.push({
            app: $(this).attr('data-app-name'),
            id: $(this).attr('data-column-id')
        });
    });
    if (colIds.length === 0) return; // Skip if no columns were found

    // Retrieve column data
    $.ajax({
        url: $('.sodar-pr-project-list-table').attr('data-custom-col-url'),
        method: 'POST',
        dataType: 'json',
        contentType : 'application/json',
        data: JSON.stringify({'projects': uuids})
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
}

// Function for updating role column
function updateRoleColumn (uuids) {
    $.ajax({
        url: $('.sodar-pr-project-list-table').attr('data-role-url'),
        method: 'POST',
        dataType: 'json',
        contentType : 'application/json',
        data: JSON.stringify({'projects': uuids})
    }).done(function (data) {
        $('.sodar-pr-project-list-item').each(function () {
            var uuid = $(this).attr('data-uuid');
            var colData = data[uuid];
            var roleCol = $(this).find('.sodar-pr-project-list-role');
            roleCol.attr('class', colData['class'])
                .text(colData['name']);
            if (colData['info']) {
                roleCol.append($('<i>')
                    .attr('class', 'iconify text-info ml-1')
                    .attr('data-icon', 'mdi:information')
                    .attr('title', colData['info'])
                );
            }
        });
    });
}

// Function for displaying message row
function showMessageRow(message) {
    $('#sodar-pr-project-list-message td').text(message);
    $('#sodar-pr-project-list-message').show();
}

// Function for hiding message row
function hideMessageRow() {
    $('#sodar-pr-project-list-message').hide();
}

// Project list data retrieval and updating
$(document).ready(function () {
    var table = $('#sodar-pr-project-list-table');
    var listUrl = table.attr('data-list-url');
    var customColAlign = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        customColAlign.push($(this).attr('data-align'));
    });
    var colCount = customColAlign.length + 2;
    var tableBody = $('#sodar-pr-project-list-table tbody');
    tableBody.append($('<tr>')
        .hide()
        .attr('id', 'sodar-pr-project-list-message')
        .append($('<td>')
            .attr('colspan', colCount)
            .attr('class', 'text-center text-muted font-italic')
        )
    );

    $.ajax({
        url: listUrl,
        method: 'GET',
    }).done(function (data) {
        $('#sodar-pr-project-list-loading').remove();

        // If there are no results, display message row
        if (data.projects.length === 0) {
            showMessageRow(data['messages']['no_projects'])
            return;
        }

        // Display rows
        $('#sodar-pr-project-list-table').addClass('sodar-card-table-borderless');
        var projectCount = data['projects'].length;
        var starredCount = 0;

        for (var i = 0; i < projectCount; i++) {
            var p = data['projects'][i];
            var icon;
            var titleClass = '';
            if (p['type'] === 'CATEGORY') {
                icon = 'rhombus-split';
                titleClass = 'text-underline';
            } else icon = 'cube';

            // Row
            tableBody.append($('<tr>')
                .attr('class',
                    'sodar-pr-project-list-item sodar-pr-project-list-item-' +
                    p['type'].toLowerCase())
                .attr('id', 'sodar-pr-project-list-item-' + p['uuid'])
                .attr('data-uuid', p['uuid'])
                .attr('data-title', p['title'])
                .attr('data-full-title', p['full_title'])
                .attr('data-starred', + p['starred'])
            );
            if (p['starred']) starredCount += 1;
            var row = tableBody.find('tr:last');

            // Title column
            row.append($('<td>')
                .append($('<div>')
                .attr('class', 'sodar-overflow-container')
                    .append($('<span>')
                        .attr('class', 'sodar-pr-project-indent')
                        .attr('style', 'padding-left: ' +
                            (p['depth'] - data['parent_depth']) * 25 + 'px;')
                    )
                    .append($('<i>')
                        .attr('class', 'iconify mr-1')
                        .attr('data-icon', 'mdi:' + icon))
                    .append($('<span>')
                        .attr('class', 'sodar-pr-project-title ' + titleClass)
                        .append($('<a>')
                            .attr('class', 'sodar-pr-project-link')
                            .attr('href', '/project/' + p['uuid'])
                            .text(p['title'])
                        )
                    )
                )
            );

            // Add icons to title columns
            var titleSpan = row.find($('span.sodar-pr-project-title'));
            // Remote icon
            if (p['remote']) {
                var textClass;
                if (p['revoked']) textClass = 'text-danger';
                else textClass = 'text-info';
                titleSpan.append($('<i>')
                    .attr('class',
                        'iconify text-info ml-2 sodar-pr-remote-project-icon ' +
                        textClass)
                    .attr('data-icon', 'mdi:cloud')
                    .attr('title', 'Remote synchronized from source site')
            );
            }
            // Public icon
            if (p['type'] === 'PROJECT' && p['public_guest_access']) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-info ml-2 sodar-pr-project-public')
                    .attr('data-icon', 'mdi:earth')
                    .attr('title', 'Public guest access')
                );
            }
            // Starred icon
            if (p['starred']) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-warning ml-2 sodar-tag-starred')
                    .attr('data-icon', 'mdi:star')
                );
            }

            // Fill project custom columns with spinners
            for (var j = 1; j < colCount - 1; j++) {
                if (p['type'] === 'PROJECT') {
                    row.append($('<td>')
                        .attr('class',
                            'sodar-pr-project-list-custom text-' +
                            customColAlign[j - 1])
                        .append($('<i>')
                            .attr('class', 'iconify spin text-muted')
                            .attr('data-icon', 'mdi:loading')
                        )
                    );
                } else row.append($('<td>'));
            }
            // Add user role column
            row.append($('<td>')
                .attr('class', 'sodar-pr-project-list-role')
                .append($('<i>')
                    .attr('class', 'iconify spin text-muted')
                    .attr('data-icon', 'mdi:loading')
                )
            );
        }

        // Enable starred button and filter
        if (starredCount > 0 && starredCount < projectCount) {
            $('#sodar-pr-project-list-link-star').prop('disabled', false);
        }
        if (projectCount > 1) {
            $('#sodar-pr-project-list-filter').prop('disabled', false);
        }

        // Get UUIDs
        var allUuids = [];
        var projectUuids = [];
        $('.sodar-pr-project-list-item').each(function () {
            var uuid = $(this).attr('data-uuid');
            allUuids.push(uuid);
            if ($(this).hasClass('sodar-pr-project-list-item-project')) {
                projectUuids.push($(this).attr('data-uuid'));
            }
        });
        if (projectUuids.length > 0) {
            // Update custom columns
            updateCustomColumns(projectUuids);
            // Update role column
            if (!data['user']['superuser']) {
                updateRoleColumn(allUuids);
            } else {
                $('.sodar-pr-project-list-role').each(function () {
                    $(this).attr('class', 'text-danger').text('Superuser');
                });
            }
            // Update overflow status
            modifyCellOverflow();
        }
    });
});

// Project list filtering
$(document).ready(function () {
    // Filter input
    $('#sodar-pr-project-list-filter').keyup(function () {
        var v = $(this).val().toLowerCase();
        var valFound = false;
        var starBtn = $('#sodar-pr-project-list-link-star');
        if (starBtn.attr('data-star-enabled') === '1') {
            starBtn.attr('data-star-enabled', '0');
            starBtn.html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');
        }

        if (v.length > 2) {
            $('#sodar-pr-project-list-filter')
                .removeClass('text-danger').addClass('text-success');
            $('.sodar-pr-project-list-item').each(function () {
                var fullTitle = $(this).attr('data-full-title');
                var titleLink = $(this).find(
                    'td:first-child div span.sodar-pr-project-title a');

                if (titleLink && fullTitle.toLowerCase().indexOf(v) !== -1) {
                    $(this).find('.sodar-pr-project-indent').hide();
                    // Reset content for updating the highlight
                    titleLink.html(fullTitle);
                    // Highlight
                    var pattern = new RegExp("(" + v + ")", "gi");
                    var titlePos = fullTitle.toLowerCase().indexOf(v);
                    if (titlePos !== -1) {
                        var titleVal = fullTitle.substring(
                            titlePos, titlePos + v.length);
                        titleLink.html(fullTitle.replace(
                            pattern,
                            '<span class="sodar-search-highlight">' +
                                titleVal + '</span>'));
                    }
                    $(this).show();
                    valFound = true;
                    hideMessageRow();
                } else {
                    $(this).hide();
                }
            });
            if (valFound === false) {
                showMessageRow('Nothing found matching the current filter.');
            } else hideMessageRow();
        } else {
            hideMessageRow();
            $('.sodar-pr-project-list-item').each(function () {
                var anchor = $(this).find('a.sodar-pr-project-link');
                var title = $(this).attr('data-title');
                if (anchor) anchor.text(title);
                else $(this).find('span.sodar-pr-project-title').text(title);
                $(this).show();
                $(this).find('.sodar-pr-project-indent').show();
            });
            $('#sodar-pr-project-list-filter').addClass(
                'text-danger').removeClass('text-success');
            starBtn.attr('data-star-enabled', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });

    // Filter by starred
    $('#sodar-pr-project-list-link-star').click(function () {
        hideMessageRow();
        $('#sodar-pr-project-list-filter').val('');

        if ($(this).attr('data-star-enabled') === '0') {
            var starCount = 0;
            $('.sodar-pr-project-list-item').each(function () {
                if ($(this).attr('data-starred') === '1') {
                  $(this).find('.sodar-pr-project-indent').hide();
                  $(this).find('a.sodar-pr-project-link').text(
                      $(this).attr('data-full-title'));
                  $(this).show();
                  starCount += 1;
                } else $(this).hide();
            });
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star"></i> Starred');
            $(this).attr('data-star-enabled', '1');
        } else if ($(this).attr('data-star-enabled') === '1') {
            $('.sodar-pr-project-list-item').each(function () {
                $(this).find('.sodar-pr-project-indent').show();
                $(this).find('a.sodar-pr-project-link').text(
                    $(this).attr('data-title'));
                $(this).show();
            });
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');
            $(this).attr('data-star-enabled', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });
});

