var D = document.querySelector('Dropzone')
D.options.myAwesomeDropzone = {
    success: function(file, response) {
        file.serverFileName = response.file_name;  // pass filename
    },
    removedfile: function (file, data) {  // triggered when remove file button was clicked
        addRemoveLinks: true,
        $.ajax({  // send AJAX request to Flask to remove file
            type:'POST',
            url:'/deletefile',
            data : {"filename" : file.serverFileName},  // pass filename
            success : function (data) {
                alert('File removed from server.')
            }
        });
    }
};