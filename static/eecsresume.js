function validateEmail(email) {
    var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function handleEmailChange() {
    if (validateEmail($("#user-email").val())) {
        $("#submit-resume").prop("disabled", false);
        $("#submit-resume").removeClass("btn-secondary");
        $("#submit-resume").addClass("btn-primary");
        $("#user-email").addClass("is-valid");
        $("#user-email").removeClass("is-invalid");
    } else {
        $("#submit-resume").prop("disabled", true);
        $("#submit-resume").removeClass("btn-primary");
        $("#submit-resume").addClass("btn-secondary");
        $("#user-email").addClass("is-invalid");
        $("#user-email").removeClass("is-valid");
    }
}

$(function() {
    // Nav bar functions
    if (window.location.href.indexOf("procedure") != -1) {
        $("#nav-procedure").addClass("active");
    } else if (window.location.href.indexOf("about") != -1) {
        $("#nav-aboutme").addClass("active");
    } else if (window.location.href.indexOf("example") != -1) {
        $("#nav-example").addClass("active");
    } else if (window.location.href.indexOf("comment") != -1) {
        $("#nav-comment").addClass("active");
    } else if (window.location.href.indexOf("article") != -1) {
        $("#nav-article").addClass("active");
    } else if (window.location.href.indexOf("maze") != -1) {
        $("#nav-maze").addClass("active");
    } else if (window.location.href.indexOf("challenge") != -1) {
        $("#nav-challenge").addClass("active");
    } else {
        $("#nav-home").addClass("active");
    }
    // Nav bar functions end
    // Main page functions
    $("#upload-file-button").click(function() {
    })  

    $("#user-email").keyup(function() {
        handleEmailChange();
    })

    $("#submit-resume").click(function(e) {
        e.preventDefault();
        handleEmailChange();
        if (!$("#submit-resume").prop("disabled")) {
            $("#upload-file-input").click();
        }
    })

    $("#upload-file-input").change(function() {
        var fileName = $('#upload-file-input')[0].files[0].name;
        var fileSize = $('#upload-file-input')[0].files[0].size;
        var fileType = $('#upload-file-input')[0].files[0].type;
        if (fileName && fileSize < 2*1024*1024 && fileType == 'application/pdf') {
            $("#main-content").addClass("d-none");
            $(".loader").removeClass("d-none");
            var fdata = new FormData($('#upload-form')[0]);
            fdata.append("email", $("#user-email").val());

            $.ajax({
                url: '/api/v1/task',
                type: 'post',
                data: fdata,
                processData: false,
                contentType: false,
                success: function(d, st, xhr) {
                    window.location.replace("./submit");
                },
                error: function(d, st, xhr) {
                    $(".loader").addClass("d-none");
                    $("#main-content").removeClass("d-none");
                    alert("服务器出现错误！请稍后再试。");
                }
            })
        } else {
            $("#upload-error-text").addClass("d-block");
        }
        
    })

    // Initialize popover
    $('#email-popover').popover({
        trigger: "focus"
    });

    // Main page functions end
    
    // Example page functions
    // Example page functions end
})
