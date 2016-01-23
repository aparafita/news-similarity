function getQS(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split('&');

  for (var i=0; i<vars.length; i++) {
    var pair = vars[i].split('=');
    if (pair[0] == variable)
      return pair[1];
  }
  return(false);
}


function isin(l, x) {
    for (var i in l)
        if (l[i] == x)
            return true;
    return false;
}