$(document).ready(function() {
    
    $("#logInForm").submit(function () {
        document.getElementById('load').style.visibility="visible";
        $("#submitBtn").attr("disabled", true);
        return true;
    });
});