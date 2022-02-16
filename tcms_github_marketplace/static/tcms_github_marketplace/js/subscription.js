$(document).ready(function () {
  $('#show-docker-password').click(function() {
    const type = $('#docker_password').attr('type')

    if (type === 'password') {
        $('#docker_password').attr('type', 'text')
    } else {
        $('#docker_password').attr('type', 'password')
    }
  })
})
