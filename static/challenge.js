submitAnswer = function(link) {
    var user = $("#username").val();
    var answer = $("#answer").val();

    if (!user) {
        alert("请输入正确的Username");
    } else if (!answer) {
        alert("请输入Answer");
    } else {
        $.ajax({
            url: '/api/v1/challenge/answer/'+link,
            type: 'post',
            data: JSON.stringify({
                'user': user,
                'answer': answer
            }),
            contentType: 'application/json',
            success: function(d, st, xhr) {
                console.log(d);
                $("#success_msg").text("上传成功，本次上传得分为"+d["score"].toString());
                $("#success_msg").removeClass("d-none");
                $("#err_msg").addClass("d-none");
            },
            error: function(d, st, xhr) {
                var text = JSON.parse(d.responseText);
                if (text && text['err_msg']) {
                    $("#err_msg").text(text['err_msg']);
                    $("#err_msg").removeClass("d-none");
                    $("#success_msg").addClass("d-none");
                } else {
                    alert("服务器出现错误！请稍后再试！");
                }
            }
        })
    }

}
$(function() {
    $("#submit-answer").click(function() {
        event.preventDefault();
        console.log($(this));
        submitAnswer($(this).attr("ques-link"));
    })
})
