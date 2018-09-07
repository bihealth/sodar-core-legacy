/*
 Javascript for projectroles and other apps utilizing its templates
 */


/* Print out human readable file size --------------------------------------- */


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


/* Bootstrap popover and tooltip setup -------------------------------------- */


// Bootstrap popover
$('[data-toggle="popover"]').popover({
    container: 'body'
});

// Bootstrap tooltip
$(function(){
    // For cases where data-toggle is also needed for another functionality
    $('[data-tooltip="tooltip"]').tooltip({
        trigger : 'hover'
    });
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});


/* Shepherd tour ------------------------------------------------------------ */


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


/* Search form setup -------------------------------------------------------- */


// Disable nav project search until 3+ characters have been input
// (not counting keyword)
function modifySearch() {
    var v = $('#sodar-nav-search-input').val();

    if(v.length > 2) {
       $('#sodar-nav-search-submit').attr('disabled', false);
    }

    else {
       $('#sodar-nav-search-submit').attr('disabled', true);
    }
}

$(document).ready(function() {
     $('#sodar-nav-search-submit').attr('disabled', 'disabled');
     $('#sodar-nav-search-input').keyup(function() {
        modifySearch();
     }).on('input', function() {
        modifySearch();
     });
 });


/* Table cell overflow handling --------------------------------------------- */


function modifyCellOverflow() {
  $('.sodar-overflow-container').each(function() {
      var parentWidth = $(this).closest('td').width();
      var lastVisibleTd = false;

      // Don't allow adding hover to last visible td for now
      if ($(this).closest('td').is($(this).closest('tr').find('td:visible:last'))) {
          lastVisibleTd = true;
      }

      if ($(this).hasClass('sodar-overflow-hover') && (
            lastVisibleTd === true || $(this).prop('scrollWidth') <= parentWidth)) {
          $(this).removeClass('sodar-overflow-hover');
      }

      else if ($(this).prop('scrollWidth') > parentWidth &&
              !$(this).hasClass('sodar-overflow-hover') &&
              !$(this).hasClass('sodar-overflow-hover-disable') &&
              lastVisibleTd === false) {
          $(this).addClass('sodar-overflow-hover');
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


/* Project list filtering --------------------------------------------------- */


// TODO: Refactor or implement with DataTables
$(document).ready(function() {
    $('.sodar-pr-home-display-filtered').hide();
    $('.sodar-pr-home-display-notfound').hide();
    $('.sodar-pr-home-display-nostars').hide();

    // Filter input
    $('#sodar-pr-project-list-filter').keyup(function () {
        v = $(this).val().toLowerCase();
        var valFound = false;
        $('.sodar-pr-home-display-nostars').hide();

        if (v.length > 2) {
            $('.sodar-pr-home-display-default').hide();
            $('#sodar-pr-project-list-filter').removeClass('text-danger').addClass('text-success');
            $('#sodar-pr-project-list-link-star').html('<i class="fa fa-star-o"></i> Starred');

            $('.sodar-pr-home-display-filtered').each(function () {
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
                        $(this).find('td:nth-child(1) div a').html(titleTxt.replace(pattern, '<span class="sodar-search-highlight">' + titleVal + '</span>'));
                    }

                    if (descPos !== -1) {
                        var descVal = descTxt.substring(descPos, descPos + v.length);
                        $(this).find('td:nth-child(2)').html(descTxt.replace(pattern, '<span class="sodar-search-highlight">' + descVal + '</span>'));
                    }

                    $(this).show();
                    valFound = true;
                    $('.sodar-pr-home-display-notfound').hide();
                }

                else {
                    $(this).hide();
                }
            });

            if (valFound === false) {
                $('.sodar-pr-home-display-notfound').show();
            }
        }

        else {
            $('.sodar-pr-home-display-default').show();
            $('.sodar-pr-home-display-filtered').hide();
            $('.sodar-pr-home-display-notfound').hide();
            $('#sodar-pr-project-list-filter').addClass(
                'text-danger').removeClass('text-success');
            $('#sodar-pr-project-list-link-star').attr('filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });

    // Filter by starred
    $('#sodar-pr-project-list-link-star').click(function () {
        $('.sodar-pr-home-display-notfound').hide();

        // Reset search terms
        $('.sodar-pr-home-display-filtered').each(function () {
            // Reset filter highlights and value
            var titleTxt = $(this).find('td:nth-child(1)').attr('orig-txt');
            var descTxt = $(this).find('td:nth-child(2)').attr('orig-txt');
            $(this).find('td:nth-child(1) a').html(titleTxt);
            $(this).find('td:nth-child(2)').html(descTxt);
            $(this).hide();
            $('#sodar-pr-project-list-filter').val('');
        });

        if ($(this).attr('filter-mode') === '0') {
            $('.sodar-pr-home-display-default').hide();
            $('.sodar-pr-home-display-starred').show();
            $('#sodar-pr-project-list-link-star').html(
                '<i class="fa fa-star"></i> Starred');
            $(this).attr('filter-mode', '1');

            if ($('.sodar-pr-home-display-starred').length === 0) {
                $('.sodar-pr-home-display-nostars').show();
            }
        }

        else if ($(this).attr('filter-mode') === '1') {
            $('.sodar-pr-home-display-nostars').hide();
            $('.sodar-pr-home-display-default').show();
            $('#sodar-pr-project-list-link-star').html(
                '<i class="fa fa-star-o"></i> Starred');
            $(this).attr('filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });
});


/* Star/unstar project ------------------------------------------------------ */


$(document).ready(function() {
    $('#sodar-pr-link-project-star').click(function () {
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
                 $('#sodar-pr-btn-star-icon').removeClass(
                     'text-muted').addClass('text-warning').removeClass(
                         'fa-star-o').addClass('fa-star');
                 $('#sodar-pr-link-project-star').attr(
                     'data-original-title', 'Unstar');
            }
            else {
                $('#sodar-pr-btn-star-icon').removeClass(
                     'text-warning').addClass('text-muted').removeClass(
                         'fa-star').addClass('fa-star-o');
                $('#sodar-pr-link-project-star').attr(
                    'data-original-title', 'Star');
            }
        }).fail(function() {
            alert('Error: unable to set project star!');
        });
    });
});


/* Make alerts removable ---------------------------------------------------- */


$('.sodar-alert-close-link').click(function () {
    $(this).closest('.sodar-alert-top').fadeOut('fast');
});


/* Improve the responsiveness of the title bar ------------------------------ */


$(window).on('resize', function() {
    if ($(this).width() < 750) {
        $('#sodar-base-navbar-nav').removeClass('ml-auto').addClass('mr-auto');
    }

    else {
        $('#sodar-base-navbar-nav').removeClass('mr-auto').addClass('ml-auto');
    }
});


/* Toggle sticky subtitle container shadow when scrolling ------------------- */


$(document).ready(function() {
    $('.sodar-app-container').scroll(function() {
        var container = $('.sodar-subtitle-container');
        var scroll = $('.sodar-app-container').scrollTop();

        if (container != null && container.hasClass('sticky-top')) {
            if (scroll >= 80) {
                container.addClass('sodar-subtitle-shadow');
            }

            else {
                container.removeClass('sodar-subtitle-shadow');
            }
        }
    });
});
