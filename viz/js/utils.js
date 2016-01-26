function getQS(variable) {
  var query = window.location.search.substring(1);
  var vars = query.split('&');

  for (var i=0; i<vars.length; i++) {
    var pair = vars[i].split('=');
    if (pair[0] == variable)
      return pair[1];
  }
  return undefined;
}


function isin(l, x) {
    for (var i in l)
        if (l[i] == x)
            return true;
    return false;
}


function isoDateToSP(date){
  var a = date.substring(0, 4),
      m = date.substring(5, 7),
      d = date.substring(8, 10);

  return d + "/" + m + "/" + a;
}


// function color(x){
//   switch(x){
//     case 0: x = '#1F83B4'; break;
//     case 1: x = '#18A188'; break;
//     case 2: x = '#54A338'; break;
//     case 3: x = '#ADB828'; break;
//     case 4: x = '#FFBD4C'; break;
//     case 5: x = '#FF9C0E'; break;
//     case 6: x = '#E75727'; break;
//     case 7: x = '#C94D8C'; break;
//     case 8: x = '#B446B3'; break;
//     case 9: x = '#8061B4'; break;
//   }
//   return x == undefined ? '#CDC9C9' : x;
// }