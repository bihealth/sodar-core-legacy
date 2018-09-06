// Set up DataTables for search tables
$(document).ready(function() {
    /*****************
     Set up DataTables
     *****************/

    $.fn.dataTable.ext.classes.sPageButton =
        'btn btn-secondary sodar-list-btn ml-1 sodar-paginate-button';

    $('.sodar-search-table').each(function() {
        $(this).DataTable({
            scrollX: false,
            paging: true,
            pageLength: window.searchPagination,
            scrollCollapse: true,
            info: false,
            language: {
                paginate: {
                    previous: '<i class="fa fa-arrow-circle-left"></i> Previous',
                    next: '<i class="fa fa-arrow-circle-right"></i> Next'
                }
            },
            dom: 'tp',
            fnDrawCallback: function() {
                // Highlight pagination
                var currentPage = $(this).DataTable().page.info().page;

                $(this).closest('.card-body').find('.sodar-paginate-button').each(function() {
                    var btnPage = $(this).text();

                    if (btnPage == currentPage + 1) {
                        $(this).removeClass('btn-secondary').addClass('btn-success');
                    }
                });

                // Update overflow status
                modifyCellOverflow();
            }
        });

        // Hide pagination if only one page
        if ($(this).DataTable().page.info().pages === 1) {
            $(this).next('.dataTables_paginate').hide();
        }

        // Display card once table has been initialized
        $(this).closest('div.sodar-search-card').show();
    });

    // Display not found once all DataTables have been initialized
    $('div#sodar-search-not-found-alert').removeClass('d-none');

    // Update overflow status
    modifyCellOverflow();

    /*********
     Filtering
     *********/

    $('.sodar-search-filter').keyup(function () {
        var dt = $(this).closest('.sodar-search-card').find('table').dataTable();
        var v = $(this).val();
        dt.fnFilter(v);
    });
});
