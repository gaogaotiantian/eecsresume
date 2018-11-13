showMaze = function(d) {
    $("#maze-jump-error").empty();
    $("#maze-jump-error").addClass("d-none");
    $("#maze-answer-error").empty();
    $("#maze-answer-error").addClass("d-none");
    $("#maze-jump-input").val("");

    $("#maze-title").text(d['data']['title']);
    $("#maze-question").text(d['data']['question']);
    $("#maze-stat").text('到达本关者' + d['data']['visit'].toString() + '位勇士，过关者' + d['data']['success'].toString() + '人')
    if (d['treasure']) {
        console.log("treasure")
        $('#maze-treasure-button').removeClass("d-none");
        $("#maze-treasure-button").attr("href", "treasure/"+d['treasure']['link']);
    } else {
        $('#maze-treasure-button').addClass("d-none");
        $("#maze-treasure-button").attr("href", "#");
    }
}
mazeJump = function() {
    var title = $("#maze-jump-input").val();
    if (title) {
        $.ajax({
            url: '/api/v1/maze/jump',
            type: 'post',
            data: JSON.stringify({
                'title': title
            }),
            contentType: 'application/json',
            success: function(d, st, xhr) {
                $("#maze-start").addClass("d-none");
                $("#maze-play").removeClass("d-none");
                showMaze(d);
            },
            error: function(d, st, xhr) {
                var text = JSON.parse(d.responseText);
                if (text && text['err_msg']) {
                    $('#maze-jump-error').removeClass("d-none");
                    $('#maze-jump-error').text(text['err_msg']);
                } else {
                    alert("服务器出现错误！请稍后再试！");
                }
            }
        })
    }
}
mazeAnswer = function() {
    var title = $("#maze-title").text();
    var answer = $("#maze-answer-input").val();
    if (title && answer) {
        $.ajax({
            url: '/api/v1/maze/answer',
            type: 'post',
            data: JSON.stringify({
                'title': title,
                'answer':answer
            }),
            contentType: 'application/json',
            success: function(d, st, xhr) {
                $("#maze-start").addClass("d-none");
                $("#maze-play").removeClass("d-none");
                showMaze(d);
            },
            error: function(d, st, xhr) {
                var text = JSON.parse(d.responseText);
                if (text && text['err_msg']) {
                    $('#maze-answer-error').removeClass("d-none");
                    $('#maze-answer-error').text(text['err_msg']);
                } else {
                    alert("服务器出现错误！请稍后再试！");
                }
            }
        })
    }
}
$(function() {
    $("#maze-jump-submit").click(function() {
        mazeJump();
    });
    $("#maze-answer-submit").click(function() {
        mazeAnswer();
    });
})
