// Update alert status
var updateAlertStatus = function () {
  var alertNav = $(document).find('#sodar-app-alert-nav');
  var statusUrl = alertNav.attr('data-status-url');
  if (statusUrl) {
      $.ajax({
          url: statusUrl,
          method: 'GET',
          dataType: 'json'
    }).done(function (data) {
      var alertBadge = alertNav.find('#sodar-app-alert-badge');
      alertBadge.find('#sodar-app-alert-count').html(data['alerts']);
      var legend = alertBadge.find('#sodar-app-alert-legend');
      if (data['alerts'] > 0) {
          $(document).find('#sodar-app-alert-badge').show();
          if (data['alerts'] === 1) legend.html('alert');
          else legend.html('alerts');
      } else $(document).find('#sodar-app-alert-badge').fadeOut(250);
    });
  }
};

$(document).ready(function () {
    // Set up alert updating
    var alertNav = $(document).find('#sodar-app-alert-nav');
    if (alertNav) {
        var alertInterval = $(document).find(
            '#sodar-app-alert-nav').attr('data-interval');
        // Update user alerts
        setInterval(function () {
            updateAlertStatus();
        }, alertInterval * 1000);
    }
});
