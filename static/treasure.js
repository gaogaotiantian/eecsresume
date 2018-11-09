treasureSubmit = function() {
    var content = $("#treasure-content").val();
    var link    = $("#treasure-content").attr("link");

    console.log(content, link)
    if (content && link) {
        $.ajax({
            url: '/api/v1/maze/treasure',
            type: 'post',
            data: JSON.stringify({
                'link': link,
                'content':content
            }),
            contentType: 'application/json',
            success: function(d, st, xhr) {
                alert("宝藏提交成功！");
                window.location.replace('/');
            },
            error: function(d, st, xhr) {
                var text = JSON.parse(d.responseText);
                if (text && text['err_msg']) {
                    $('#treasure-error').removeClass("d-none");
                    $('#treasure-error').text(text['err_msg']);
                } else {
                    alert("服务器出现错误！请稍后再试！");
                }
            }
        })
    }
}

$(function() {
    $("#treasure-submit").click(function() {
        treasureSubmit();
    })
})
