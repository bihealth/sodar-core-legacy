/*
 General SODAR Core / projectroles javascript
 */


/* Cross Site Request Forgery protection for Ajax views --------------------- */


// From: https://stackoverflow.com/a/47878344
var csrfToken = jQuery("[name=csrfmiddlewaretoken]").val();

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// set CSRF header
$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        }
    }
});


/* Print out human readable file size --------------------------------------- */


// From: https://stackoverflow.com/a/14919494
function humanFileSize(bytes, si) {
    var thresh = si ? 1000 : 1024;
    if (Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    var units = si
        ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
        : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while (Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1) + ' ' + units[u];
}


/* Bootstrap popover and tooltip setup -------------------------------------- */


// Bootstrap popover
$('[data-toggle="popover"]').popover({
    container: 'body',
    sanitize: false
});

// Bootstrap tooltip
$(function () {
    // For cases where data-toggle is also needed for another functionality
    $('[data-tooltip="tooltip"]').tooltip({
        trigger: 'hover'
    });
    $('[data-toggle="tooltip"]').tooltip({
        trigger: 'hover'
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
$(document).ready(function () {
    if (tourEnabled === false) {
        $('#site-help-link').addClass('disabled').removeClass('text-warning');
    }

    $('#site-help-link').click(function () {
        tour.start();
    });
});


/* Search form setup -------------------------------------------------------- */


// Disable nav project search until 3+ characters have been input
// (not counting keyword)
function modifySearch() {
    var v = $('#sodar-nav-search-input').val();
    if (v.trim().length > 2) {
        $('#sodar-nav-search-submit').attr('disabled', false);
    } else {
        $('#sodar-nav-search-submit').attr('disabled', true);
    }
}

$(document).ready(function () {
    var searchInput = $('#sodar-nav-search-input');

    if (searchInput) {
        if (!searchInput.val() || searchInput.val().length === 0) {
            $('#sodar-nav-search-submit').attr('disabled', true);
        } else {
            $('#sodar-nav-search-submit').attr('disabled', false);
        }
        searchInput.keyup(function () {
            modifySearch();
        }).on('input', function () {
            modifySearch();
        });
    }
});


/* Table cell overflow handling --------------------------------------------- */


function modifyCellOverflow() {
    $('.sodar-overflow-container').each(function () {
        var parentWidth = $(this).parent().prop('scrollWidth');
        var lastVisibleTd = false;

        // Don't allow adding hover to last visible td for now
        if ($(this).parent().is($(this).closest('td')) &&
            $(this).closest('td').is($(this).closest('tr').find('td:visible:last'))) {
            lastVisibleTd = true;
        }
        if ($(this).hasClass('sodar-overflow-hover') && (
            lastVisibleTd === true || $(this).prop('scrollWidth') <= parentWidth)) {
            $(this).removeClass('sodar-overflow-hover');
        } else if ($(this).prop('scrollWidth') > parentWidth &&
            !$(this).hasClass('sodar-overflow-hover') &&
            !$(this).hasClass('sodar-overflow-hover-disable') &&
            lastVisibleTd === false) {
            $(this).addClass('sodar-overflow-hover');
        }
    });
}

// On document load, enable/disable all overflow containers
$(document).ready(function () {
    modifyCellOverflow();
});

// On window resize, enable/disable all overflow containers
$(window).resize(function () {
    if (typeof (window.refreshCellOverflow) === 'undefined' ||
        window.refreshCellOverflow !== false) {
        modifyCellOverflow();
    }
});


/* Improve the responsiveness of the title bar ------------------------------ */


$(window).on('resize', function () {
    if ($(this).width() < 750) {
        $('#sodar-base-navbar-nav').removeClass('ml-auto').addClass('mr-auto');
    } else {
        $('#sodar-base-navbar-nav').removeClass('mr-auto').addClass('ml-auto');
    }
});


/* Toggle sticky subtitle container shadow when scrolling ------------------- */


$(document).ready(function () {
    $('.sodar-app-container').scroll(function () {
        var container = $('.sodar-subtitle-container');
        var scroll = $('.sodar-app-container').scrollTop();

        if (container != null && container.hasClass('sticky-top')) {
            if (scroll >= 80) {
                container.addClass('sodar-subtitle-shadow');
            } else {
                container.removeClass('sodar-subtitle-shadow');
            }
        }
    });
});


/* Initialize Clipboard.js for common buttons ------------------------------- */


$(document).ready(function() {
    /***************
     Init Clipboards
     ***************/
    new ClipboardJS('.sodar-copy-btn');

    /******************
     Copy link handling
     ******************/
    $('.sodar-copy-btn').click(function () {
        // NOTE: Temporary hack, see issue #333
        var icon = $(this).find('i');
        var mutedRemoved = false;

        // Title bar links are currently rendered a bit differently
        if (icon.hasClass('text-muted')) {
            icon.removeClass('text-muted');
            mutedRemoved = true;
        }

        icon.addClass('text-warning');

        var realTitle = $(this).tooltip().attr('data-original-title');
        $(this).attr('title', 'Copied!')
            .tooltip('_fixTitle')
            .tooltip('show')
            .attr('title', realTitle)
            .tooltip('_fixTitle');

        $(this).delay(250).queue(function() {
            icon.removeClass('text-warning');

            if (mutedRemoved) {
                icon.addClass('text-muted');
            }

            $(this).dequeue();
        });
    });
});


/* Display unsupported browser warning -------------------------------------- */


$(document).ready(function () {
    if (window.sodarBrowserWarning === 1) {
        // Based on https://stackoverflow.com/a/38080051
        navigator.browserSpecs = (function(){
            var ua = navigator.userAgent, tem,
                M = ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
            if(/trident/i.test(M[1])) {
                tem = /\brv[ :]+(\d+)/g.exec(ua) || [];
                return {name: 'IE', version: (tem[1] || '')};
            }
            if(M[1] === 'Chrome'){
                tem = ua.match(/\b(OPR|Edge)\/(\d+)/);
                if (tem != null) return {name: tem[1].replace(
                    'OPR', 'Opera'), version: tem[2]};
            }
            M = M[2] ? [M[1], M[2]]: [navigator.appName, navigator.appVersion, '-?'];
            if ((tem = ua.match(/version\/(\d+)/i)) != null)
                M.splice(1, 1, tem[1]);
            return {name: M[0], version: M[1]};
        })();

        if (!['Chrome', 'Firefox', 'Edge'].includes(navigator.browserSpecs.name)) {
            let parentElem = $('div.sodar-app-container');

            if (!parentElem.length) {
                parentElem = $('div.sodar-content-container').find(
                    'div.container-fluid').first();
            }

            if (!$('div.sodar-alert-container').length) {
                parentElem.prepend(
                    '<div class="container-fluid sodar-alert-container"></div>');
            }

            $('div.sodar-alert-container').prepend(
                '<div class="alert alert-danger sodar-alert-top">' +
                '<i class="iconify" data-icon="mdi:alert"></i> ' +
                'You are using an unsupported browser. We recommend using ' +
                'a recent version of ' +
                '<a href="https://www.mozilla.org/firefox/new" target="_blank">Mozilla Firefox</a> or ' +
                '<a href="https://www.google.com/chrome" target="_blank">Google Chrome</a>.' +
                '</div>');
        }
    }
});


/* Hide sidebar based on element count -------------------------------------- */


function toggleSidebar() {
    if (window.sidebar && !window.sidebar.is(':visible')) {
        if (window.sidebarMinWindowHeight < window.innerHeight &&
                window.innerWidth > 1000) {
            window.sidebar.show();
            window.sidebar_alt_btn.hide();
        }
    } else if (window.sidebarMinWindowHeight > window.innerHeight ||
            window.innerWidth < 1000) {
        window.sidebar_alt_btn.show();
        window.sidebar.hide();
    }
}

$(document).ready(function () {
    // Remember sidebar total height
    window.sidebar = $('#sodar-pr-sidebar');
    window.sidebar_alt_btn = $('#sodar-pr-sidebar-alt-btn');
    let sidebarContent = $('#sodar-pr-sidebar-navbar').get(0);
    if (sidebarContent)
        window.sidebarMinWindowHeight = sidebarContent.scrollHeight + sidebarContent.getBoundingClientRect().top;
    toggleSidebar();

});

$(window).on('resize', function () {
    toggleSidebar();
});
