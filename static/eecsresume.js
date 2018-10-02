$(function() {
    $("#upload-file-button").click(function() {
        console.log("click")
        var fileSize = $('#upload-file-input')[0].files[0].size;
        if (fileSize < 2*1024*1024) {
            var fdata = new FormData($('#upload-form')[0]);

            $.ajax({
                url: '/api/v1/task',
                type: 'post',
                data: fdata,
                processData: false,
                contentType: false,
                success: function(d, st, xhr) {
                    console.log("success!");
                },
                error: function(d, st, xhr) {
                    console.log("error!");
                }
            })
        }
    })  
})
