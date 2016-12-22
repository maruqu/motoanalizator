var map;
var geocoder;
var data;
var markers = [];

function initialize() {
  geocoder = new google.maps.Geocoder();
  var latlng = new google.maps.LatLng(52.2296756, 21.0122287);
  var mapOptions = {
    zoom: 6,
    center: latlng
  }
  map = new google.maps.Map(document.getElementById('map'), mapOptions);
};


function placeMarkers() {
  cities = data.locationData;
  for (var i = 0; i < cities.labels.length; i++) {
    if(cities.labels[i].lat == 0)
      continue;
    else{
      for (var j = 0; j < cities.series[i]; j++) {
        var marker = new google.maps.Marker({
          map: map,
          position: cities.labels[i]
        });
        markers.push(marker);
      };
    };
  };
  var markerCluster = new MarkerClusterer(map, markers,
    {imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'});
};



function renderCharts(){
  new Chartist.Line('#chart_year_price', data.yearPrice,{
    plugins: [
    Chartist.plugins.ctPointLabels({
      textAnchor: 'middle'
    })
    ]
  });
  new Chartist.Line('#chart_year_milage', data.yearMilage, {
    plugins: [
    Chartist.plugins.ctPointLabels({
      textAnchor: 'middle'
    })
    ]
  });

  new Chartist.Bar('#chart_year_quantity', data.yearQuantity , {
    stackBars: true,
    axisY: {
      labelInterpolationFnc: function(value) {
        return (value);
      }
    }
  }).on('draw', function(data) {
    if(data.type === 'bar') {
      data.element.attr({
        style: 'stroke-width: 30px'
      });
    }
  });

  new Chartist.Pie('#chart_fuel_type', data.fuelType,{
    plugins: [
    Chartist.plugins.ctPointLabels({
      textAnchor: 'middle'
    })
    ]
  });
}
