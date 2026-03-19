// Copyright (c) 2022 Alexander Todorov <atodorov@otb.bg>
//
// Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
// https://www.gnu.org/licenses/agpl-3.0.html

$(document).ready(function () {
    // collapse all child rows
    $('.tree-list-view-pf').find(".list-group-item-container").addClass('hidden');

    // click the list-view heading then expand a row
    $('.list-group-item-header').click(function (event) {
      if(!$(event.target).is('button, a, input, .fa-ellipsis-v')) {
        var $this = $(this);
        $this.find('.fa-angle-right').toggleClass('fa-angle-down');
        var $itemContainer = $this.siblings('.list-group-item-container');
        if ($itemContainer.children().length) {
          $itemContainer.toggleClass('hidden');
        }
      }
    });

  // toggle docker password
  $('#show-docker-password').click(function() {
    var input_type = $('#docker_password').attr('type')

    if (input_type === 'password') {
        $('#docker_password').attr('type', 'text')
    } else {
        $('#docker_password').attr('type', 'password')
    }
  })

  // toggle private repo password
  $('#show-repo-token').click(function() {
    var input_type = $('#repo_token').attr('type')

    if (input_type === 'password') {
        $('#repo_token').attr('type', 'text')
    } else {
        $('#repo_token').attr('type', 'password')
    }
  })
})
