(function() {

  // This function sets up the auto-complete functionality.
  function setup_completion() {
    // The template is stored in the HTML.
    var template = $("#template").html();
    Mustache.parse(template);

    // This object executes and formats the searches.
    var search = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace("title"),
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      remote: {url: '/complete?q=%QUERY',
               filter: function(resp){return resp.results}}
    });
    search.initialize();

    // This is the interface to the input.
    $('#typeahead').typeahead(null, {
      name:"autocomplete",
      minLength:3,
      hint:false,
      source:search.ttAdapter(),
      templates:{suggestion: function(o){return Mustache.render(template, o)}}
    }).on("typeahead:selected", function (e, o) {
      // When one of the results is selected.
      console.log(o.title);
      window.location = "/stream/" + o.id;
    });
  }

  // Run when ready.
  $(setup_completion);

})();
