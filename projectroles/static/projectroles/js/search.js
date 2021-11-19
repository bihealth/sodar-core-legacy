// Set up DataTables for search tables
$(document).ready(function() {
    /*****************
     Set up DataTables
     *****************/

    $.fn.dataTable.ext.classes.sPageButton =
        'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light text-primary';

    $('.sodar-search-table').each(function() {
        $(this).DataTable({
            scrollX: false,
            paging: true,
            pageLength: window.searchPagination,
            lengthChange: true,
            scrollCollapse: true,
            info: false,
            language: {
                paginate: {
                    previous: '<i class="iconify text-primary" ' +
                        'data-icon="mdi:arrow-left-circle"></i> Prev',
                    next: '<i class="iconify text-primary" ' +
                        'data-icon="mdi:arrow-right-circle"></i> Next'
                }
            },
            dom: 'tp',
            fnDrawCallback: function() {
                modifyCellOverflow();
            }
        });

        // Hide pagination and disable page dropdown if only one page
        if ($(this).DataTable().page.info().pages === 1) {
            $(this).closest('.sodar-search-card')
                .find('.sodar-search-page-length').prop('disabled', 'disabled');
            $(this).next('.dataTables_paginate').hide();
        }

        // Display card once table has been initialized
        $(this).closest('div.sodar-search-card').show();
    });

    // Display not found once all DataTables have been initialized
    $('div#sodar-search-not-found-alert').removeClass('d-none');

    // Update overflow status
    modifyCellOverflow();

    /**********
     Pagination
     **********/

    $('.sodar-search-page-length').change(function () {
        var dt = $(this).closest('.sodar-search-card').find('table').DataTable();
        var value = parseInt($(this).val());
        dt.page.len(value).draw();
    });

    /*********
     Filtering
     *********/

    $('.sodar-search-filter').keyup(function () {
        var dt = $(this).closest('.sodar-search-card').find('table').dataTable();
        var v = $(this).val();
        dt.fnFilter(v);
    });
});
