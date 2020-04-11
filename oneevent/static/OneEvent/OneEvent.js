// Thank you http://stackoverflow.com/questions/24469602/how-to-prevent-accordion-from-toggling-when-button-in-header-is-clicked
avoid_collapse_toggle = function(e) {
    e.stopPropagation();
};

hide_cancelled_toggle = function(evt){
    $('tr.cancelled').toggleClass("hidden", !evt.target.checked);
    avoid_collapse_toggle(evt);
};

add_message = function(level, text){
    var newMsg = $("#alert-template").clone()
    newMsg.addClass("alert-"+level)
    newMsg.removeAttr("id")
    newMsg.removeClass("hidden")
    newMsg.prepend("<span>" + text + "</span>")
    $('#messages-row').append(newMsg)
};

send_invite = function(url, username){
    var jqxhr = $.ajax(url)
       .done(function() {
            add_message('success', 'Invite sent to ' + username)
       })
       .fail(function() {
            add_message('danger', 'Failed sending invite to ' + username)
       });
};

//Thanks to http://stackoverflow.com/questions/400212/how-do-i-copy-to-the-clipboard-in-javascript
copyToClipboard = function(text) {
    window.prompt("Copy to clipboard: Ctrl+C, Enter", text);
}
