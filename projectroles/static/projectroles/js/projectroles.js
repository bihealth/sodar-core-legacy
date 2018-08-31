/*
 Javascript for projectroles and other apps utilizing its templates
 */


// Print out human readable file size ------------------------------------------


// From: https://stackoverflow.com/a/14919494
function humanFileSize(bytes, si) {
    var thresh = si ? 1000 : 1024;
    if(Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    var units = si
        ? ['kB','MB','GB','TB','PB','EB','ZB','YB']
        : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1)+' '+units[u];
}


// Shepherd tour ---------------------------------------------------------------


var tourEnabled = false;  // Needs to set true if there is content
tour = new Shepherd.Tour({
    defaults: {
            classes: 'shepherd-theme-default'
        }
});

// Set up tour link
$(document).ready(function() {
    if (tourEnabled === false) {
        $('#site-help-link').addClass(
            'disabled').removeClass('text-warning');
    }

    $('#site-help-link').click(function() {
        tour.start();
    });
});


// Search form setup -----------------------------------------------------------


// Disable nav project search until 3+ characters have been input
// (not counting keyword)
function modifySearch() {
    var v = $('#omics-nav-search-input').val();

    if(v.length > 2) {
       $('#omics-nav-search-submit').attr('disabled', false);
    }

    else {
       $('#omics-nav-search-submit').attr('disabled', true);
    }
}

$(document).ready(function() {
     $('#omics-nav-search-submit').attr('disabled', 'disabled');
     $('#omics-nav-search-input').keyup(function() {
        modifySearch();
     }).on('input', function() {
        modifySearch();
     });
 });


// Table cell overflow handling ------------------------------------------------


function modifyCellOverflow() {
  $('.omics-overflow-container').each(function() {
      var parentWidth = $(this).closest('td').width();
      var lastVisibleTd = false;

      // Don't allow adding hover to last visible td for now
      if ($(this).closest('td').is($(this).closest('tr').find('td:visible:last'))) {
          lastVisibleTd = true;
      }

      if ($(this).hasClass('omics-overflow-hover') && (
            lastVisibleTd === true || $(this).prop('scrollWidth') <= parentWidth)) {
          $(this).removeClass('omics-overflow-hover');
      }

      else if ($(this).prop('scrollWidth') > parentWidth &&
              !$(this).hasClass('omics-overflow-hover') &&
              !$(this).hasClass('omics-overflow-hover-disable') &&
              lastVisibleTd === false) {
          $(this).addClass('omics-overflow-hover');
      }
  });
}

// On document load, enable/disable all overflow containers
$(document).ready(function() {
    modifyCellOverflow();
});

// On window resize, enable/disable all overflow containers
$(window).resize(function() {
    if (typeof(window.refreshCellOverflow) === 'undefined' ||
            window.refreshCellOverflow !== false) {
        modifyCellOverflow();
    }
});


// Project list filtering ------------------------------------------------------


// TODO: Refactor or implement with DataTables
$(document).ready(function() {
    $('.omics-pr-home-display-filtered').hide();
    $('.omics-pr-home-display-notfound').hide();
    $('.omics-pr-home-display-nostars').hide();

    // Filter input
    $('#omics-pr-project-list-filter').keyup(function () {
        v = $(this).val().toLowerCase();
        var valFound = false;
        $('.omics-pr-home-display-nostars').hide();

        if (v.length > 2) {
            $('.omics-pr-home-display-default').hide();
            $('#omics-pr-project-list-filter').removeClass('text-danger').addClass('text-success');
            $('#omics-pr-project-list-link-star').html('<i class="fa fa-star-o"></i> Starred');

            $('.omics-pr-home-display-filtered').each(function () {
                var titleTxt = $(this).find('td:nth-child(1)').attr('orig-txt');
                var descTxt = $(this).find('td:nth-child(2)').attr('orig-txt');

                if ($(this).find('td:nth-child(1) div a').text().toLowerCase().indexOf(v) !== -1 ||
                    $(this).find('td:nth-child(2)').text().toLowerCase().indexOf(v) !== -1) {
                    // Reset content for updating the highlight
                    $(this).find('td:nth-child(1) div a').html(titleTxt);
                    $(this).find('td:nth-child(2)').html(descTxt);

                    // Highlight
                    var pattern = new RegExp("(" + v + ")", "gi");
                    var titlePos = titleTxt.toLowerCase().indexOf(v);
                    var descPos = descTxt.toLowerCase().indexOf(v);

                    if (titlePos !== -1) {
                        var titleVal = titleTxt.substring(titlePos, titlePos + v.length);
                        $(this).find('td:nth-child(1) div a').html(titleTxt.replace(pattern, '<span class="omics-search-highlight">' + titleVal + '</span>'));
                    }

                    if (descPos !== -1) {
                        var descVal = descTxt.substring(descPos, descPos + v.length);
                        $(this).find('td:nth-child(2)').html(descTxt.replace(pattern, '<span class="omics-search-highlight">' + descVal + '</span>'));
                    }

                    $(this).show();
                    valFound = true;
                    $('.omics-pr-home-display-notfound').hide();
                }

                else {
                    $(this).hide();
                }
            });

            if (valFound === false) {
                $('.omics-pr-home-display-notfound').show();
            }
        }

        else {
            $('.omics-pr-home-display-default').show();
            $('.omics-pr-home-display-filtered').hide();
            $('.omics-pr-home-display-notfound').hide();
            $('#omics-pr-project-list-filter').addClass('text-danger').removeClass('text-success');
            $('#omics-pr-project-list-link-star').attr('filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });

    // Filter by starred
    $('#omics-pr-project-list-link-star').click(function () {
        $('.omics-pr-home-display-notfound').hide();

        // Reset search terms
        $('.omics-pr-home-display-filtered').each(function () {
            // Reset filter highlights and value
            var titleTxt = $(this).find('td:nth-child(1)').attr('orig-txt');
            var descTxt = $(this).find('td:nth-child(2)').attr('orig-txt');
            $(this).find('td:nth-child(1) a').html(titleTxt);
            $(this).find('td:nth-child(2)').html(descTxt);
            $(this).hide();
            $('#omics-pr-project-list-filter').val('');
        });

        if ($(this).attr('filter-mode') === '0') {
            $('.omics-pr-home-display-default').hide();
            $('.omics-pr-home-display-starred').show();
            $('#omics-pr-project-list-link-star').html('<i class="fa fa-star"></i> Starred');
            $(this).attr('filter-mode', '1');

            if ($('.omics-pr-home-display-starred').length === 0) {
                $('.omics-pr-home-display-nostars').show();
            }
        }

        else if ($(this).attr('filter-mode') === '1') {
            $('.omics-pr-home-display-nostars').hide();
            $('.omics-pr-home-display-default').show();
            $('#omics-pr-project-list-link-star').html('<i class="fa fa-star-o"></i> Starred');
            $(this).attr('filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });
});


// Star/unstar project ---------------------------------------------------------


$(document).ready(function() {
    $('#omics-pr-link-project-star').click(function () {
        $.post({
            url: $(this).attr('star-url'),
            method: 'POST',
            dataType: 'json',
            headers: {
                'X-CSRFToken': $(this).attr('csrf-token')
            }
        }).done(function (data) {
            console.log('Star clicked: ' + data);  // DEBUG
            if (data === 1) {
                 $('#omics-pr-btn-star-icon').removeClass(
                     'text-muted').addClass('text-warning').removeClass(
                         'fa-star-o').addClass('fa-star');
                 $('#omics-pr-link-project-star').attr('data-original-title', 'Unstar');
            }
            else {
                $('#omics-pr-btn-star-icon').removeClass(
                     'text-warning').addClass('text-muted').removeClass(
                         'fa-star').addClass('fa-star-o');
                $('#omics-pr-link-project-star').attr('data-original-title', 'Star');
            }
        }).fail(function() {
            alert('Error: unable to set project star!');
        });
    });
});


// Make alerts removable -------------------------------------------------------


$('.omics-alert-close-link').click(function () {
    $(this).closest('.omics-alert-top').fadeOut('fast');
});


// Improve the responsiveness of the title bar ---------------------------------


$(window).on('resize', function() {
    if ($(this).width() < 750) {
        $('#omics-base-navbar-nav').removeClass('ml-auto').addClass('mr-auto');
    }

    else {
        $('#omics-base-navbar-nav').removeClass('mr-auto').addClass('ml-auto');
    }
});


// Enable/disable sticky subtitle container shadow when scrolling --------------


$(document).ready(function() {
    $('.omics-app-container').scroll(function() {
        var container = $('.omics-subtitle-container');
        var scroll = $('.omics-app-container').scrollTop();

        if (container != null && container.hasClass('sticky-top')) {
            if (scroll >= 80) {
                container.addClass('omics-subtitle-shadow');
            }

            else {
                container.removeClass('omics-subtitle-shadow');
            }
        }
    });
});
