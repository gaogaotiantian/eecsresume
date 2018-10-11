getCardDom = function(result) {
    var type = "某人";
    if (result['type'] == "anonymous") {
        type = '匿名客户';
    } else if (result['type'] == "browse") {
        type = "点评客户";
    } else if (result['type'] == "review") {
        type = "修改客户";
    } 
    $card = $('#card-tmpl').clone();
    $card.removeClass('d-none');
    $card.removeAttr('id');
    $card.find('.card-email').text(result['email']);
    $card.find('.card-usertype').text(type);
    $card.find('.card-time').text(result['edit_time']);
    $card.find('.card-score').text(result['score'] + ' / 10');
    $card.find('.card-comment').text(result['comment']);

    return $card
}

changePagination = function(currPage = 1, totalPage = 3) {
    var $pagination = $('.pagination');
    $pagination.empty();
    for (var i = Math.max(1, currPage-2); i <= Math.min(totalPage, currPage+2); i++) {
        var $page_item = $('<li>', {class:"page-item"});
        if (i == currPage) {
            $page_item.addClass("active");
        }
        $page_item.append($('<a>', {class:"page-link", href:"#"}).text(i));
        $pagination.append($page_item);
    }
}

showComment = function(page = 1) {
    $.ajax({
        url: '/api/v1/comment',
        type: 'get',
        data: {'page':page},
        success: function(d, st, xhr) {
            var $comment_body = $('#comment-body');
            $comment_body.empty();
            for (i in d['results']) {
                var result = d['results'][i];
                $card = getCardDom(result);
                $comment_body.append($card);
            }
            changePagination(page, d['totalPage']);
            $('#average-score').text(d['avrScore']);
        },
        error: function(d, st, xhr) {
            alert("服务器出现错误！请稍后再试。");
        }
    })
}

submitComment = function() {
    var email = "";
    if ($('#email-checkbox').prop('checked')) {
        email = "anonymous";
    } else if (validateEmail($('#email-input').val())) {
        email = $('#email-input').val();
    } else {
        alert("请输入正确的Email地址！");
        return;
    }

    $.ajax({
        url: '/api/v1/comment',
        type: 'post',
        data: JSON.stringify({
            'email': email,
            'comment': $('#comment-textarea').val(),
            'score': parseInt($('#grade-slider').val())/100
        }),
        contentType: 'application/json',
        success: function(d, st, xhr) {
            window.location.replace('./comment');
        },
        error: function(d, st, xhr) {
            var text = JSON.parse(d.responseText);
            if (text && text['err_msg']) {
                alert(text['err_msg']);
            } else {
                alert("服务器出现错误！请稍后再试！");
            }
        }
    })
}
$(function() {

    $('header').removeClass("mb-auto");
    showComment();
    $('body').on("click", ".page-link",function() {
        showComment(parseInt($(this).text()));
    })    

    $('#email-checkbox').click(function() {
        if ($(this).prop("checked")) {
            $('#email-input').prop('disabled', true);
        } else {
            $('#email-input').prop('disabled', false);
        }
    })

    $('#grade-slider').change(function() {
        $('#grade-value').text(parseInt($(this).val())/100);
    })

    $('#comment-submit').click(function(event) {
        event.preventDefault();
        submitComment();
    })
})
