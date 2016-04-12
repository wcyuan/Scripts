//
// This is a Google Scripts App-Script for calculating directions and distance using the Maps service
// It is mostly based on the provided examples and tutorials
//

// This is modified from https://developers.google.com/apps-script/quickstart/macros#set_it_up

/**
 * A custom function that converts meters to miles.
 *
 * @param {Number} meters The distance in meters.
 * @return {Number} The distance in miles.
 */
function metersToMiles(meters) {
  if (typeof meters != 'number') {
    return null;
  }
  return meters / 1000 * 0.621371;
}

/**
 * A shared helper function used to obtain the full set of directions
 * information between two addresses. Uses the Apps Script Maps Service.
 *
 * @param {String} origin The starting address.
 * @param {String} destination The ending address.
 * @return {Object} The directions response object.
 */
function getDirections_(origin, destination, mode) {
  if (typeof mode == 'undefined') {
    mode = Maps.DirectionFinder.Mode.WALKING;
  }
  var directionFinder = Maps.newDirectionFinder();
  directionFinder.setOrigin(origin);
  directionFinder.setDestination(destination);
  directionFinder.setMode(Maps.DirectionFinder.Mode.WALKING);
  var directions = directionFinder.getDirections();
  if (directions.routes.length == 0) {
    throw 'Unable to calculate directions between these addresses.';
  }
  return directions;
}

/**
 * A custom function that gets the driving distance between two addresses.
 *
 * @param {String} origin The starting address.
 * @param {String} destination The ending address.
 * @return {Number} The distance in meters.
 */
function walkingDistance(origin, destination) {
  var directions = getDirections_(origin, destination, Maps.DirectionFinder.Mode.WALKING);
  return directions.routes[0].legs[0].distance.value;
}

/**
 * Return the lat lng for a string
 */
function getGeocode(name) {
  geoResults = Maps.newGeocoder().geocode(name);

  var retval = {};
  // Get the latitude and longitude
  retval.lat = geoResults.results[0].geometry.location.lat;
  retval.lng = geoResults.results[0].geometry.location.lng;

  return retval;
}

/**
 * Return the approximate address given a lat lng
 */
function reverseGeocode(lat, lng) {
 // Gets the address of an area around Central Park.
 var response = Maps.newGeocoder().reverseGeocode(lat, lng, lat, lng);
 for (var i = 0; i < response.results.length; i++) {
   var result = response.results[i];
   Logger.log('%s: %s, %s', result.formatted_address, result.geometry.location.lat,
       result.geometry.location.lng);
 }
 return result.formatted_address;
}

/**
 * Return an address given a name
 * Doesn't work that well...
 */
function getAddress(name) {
  geoResults = Maps.newGeocoder().geocode(name);

  return geoResults.results[0].formatted_address;
  
  //var geo = getGeocode(name);
  //return reverseGeocode(geo.lat, geo.lng);
}

/**
 * A special function that runs when the spreadsheet is open, used to add a
 * custom menu to the spreadsheet.
 */
function onOpen() {
  var spreadsheet = SpreadsheetApp.getActive();
  var menuItems = [
    {name: 'Generate step-by-step...', functionName: 'generateStepByStep_'}
  ];
  spreadsheet.addMenu('Directions', menuItems);
}

/**
 * Creates a new sheet containing step-by-step directions between the two
 * addresses on the "Settings" sheet that the user selected.
 */
function generateStepByStep_() {
  var spreadsheet = SpreadsheetApp.getActive();
  var settingsSheet = spreadsheet.getSheetByName('Settings');
  settingsSheet.activate();

  // Prompt the user for a row number.
  var selectedRow = Browser.inputBox('Generate step-by-step',
      'Please enter the row number of the addresses to use' +
      ' (for example, "2"):',
      Browser.Buttons.OK_CANCEL);
  if (selectedRow == 'cancel') {
    return;
  }
  var rowNumber = Number(selectedRow);
  if (isNaN(rowNumber) || rowNumber < 2 ||
      rowNumber > settingsSheet.getLastRow()) {
    Browser.msgBox('Error',
        Utilities.formatString('Row "%s" is not valid.', selectedRow),
        Browser.Buttons.OK);
    return;
  }

  // Retrieve the addresses in that row.
  var row = settingsSheet.getRange(rowNumber, 1, 1, 2);
  var rowValues = row.getValues();
  var origin = rowValues[0][0];
  var destination = rowValues[0][1];
  if (!origin || !destination) {
    Browser.msgBox('Error', 'Row does not contain two addresses.',
        Browser.Buttons.OK);
    return;
  }

  // Get the raw directions information.
  var directions = getDirections_(origin, destination);

  // Create a new sheet and append the steps in the directions.
  var sheetName = 'Driving Directions for Row ' + rowNumber;
  var directionsSheet = spreadsheet.getSheetByName(sheetName);
  if (directionsSheet) {
    directionsSheet.clear();
    directionsSheet.activate();
  } else {
    directionsSheet =
        spreadsheet.insertSheet(sheetName, spreadsheet.getNumSheets());
  }
  var sheetTitle = Utilities.formatString('Driving Directions from %s to %s',
      origin, destination);
  var headers = [
    [sheetTitle, '', ''],
    ['Step', 'Distance (Meters)', 'Distance (Miles)']
  ];
  var newRows = [];
  for (var i = 0; i < directions.routes[0].legs[0].steps.length; i++) {
    var step = directions.routes[0].legs[0].steps[i];
    // Remove HTML tags from the instructions.
    var instructions = step.html_instructions.replace(/<br>|<div.*?>/g, '\n')
        .replace(/<.*?>/g, '');
    newRows.push([
      instructions,
      step.distance.value
    ]);
  }
  directionsSheet.getRange(1, 1, headers.length, 3).setValues(headers);
  directionsSheet.getRange(headers.length + 1, 1, newRows.length, 2)
      .setValues(newRows);
  directionsSheet.getRange(headers.length + 1, 3, newRows.length, 1)
      .setFormulaR1C1('=METERSTOMILES(R[0]C[-1])');

  // Format the new sheet.
  directionsSheet.getRange('A1:C1').merge().setBackground('#ddddee');
  directionsSheet.getRange('A1:2').setFontWeight('bold');
  directionsSheet.setColumnWidth(1, 500);
  directionsSheet.getRange('B2:C').setVerticalAlignment('top');
  directionsSheet.getRange('C2:C').setNumberFormat('0.00');
  var stepsRange = directionsSheet.getDataRange()
      .offset(2, 0, directionsSheet.getLastRow() - 2);
  setAlternatingRowBackgroundColors_(stepsRange, '#ffffff', '#eeeeee');
  directionsSheet.setFrozenRows(2);
  SpreadsheetApp.flush();
}

/**
 * Sets the background colors for alternating rows within the range.
 * @param {Range} range The range to change the background colors of.
 * @param {string} oddColor The color to apply to odd rows (relative to the
 *     start of the range).
 * @param {string} evenColor The color to apply to even rows (relative to the
 *     start of the range).
 */
function setAlternatingRowBackgroundColors_(range, oddColor, evenColor) {
  var backgrounds = [];
  for (var row = 1; row <= range.getNumRows(); row++) {
    var rowBackgrounds = [];
    for (var column = 1; column <= range.getNumColumns(); column++) {
      if (row % 2 == 0) {
        rowBackgrounds.push(evenColor);
      } else {
        rowBackgrounds.push(oddColor);
      }
    }
    backgrounds.push(rowBackgrounds);
  }
  range.setBackgrounds(backgrounds);
}



// The below is from
// https://developers.google.com/apps-script/articles/maps_tutorial#generating-driving-directions


function restaurantLocationsMap() {
  // Get the sheet named 'restaurants'
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('restaurants');

  // Store the restaurant name and address data in a 2-dimensional array called
  // restaurantInfo. This is the data in cells A2:B4
  var restaurantInfo = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues();

  // Create a new StaticMap
  var restaurantMap = Maps.newStaticMap();

  // Create a new UI Application, which we use to display the map
  var ui = UiApp.createApplication();

  // Create a grid widget to use for displaying the text of the restaurant names
  // and addresses. Start by populating the header row in the grid.
  var grid = ui.createGrid(restaurantInfo.length + 1, 3);
  grid.setWidget(0, 0, ui.createLabel('Store #').setStyleAttribute('fontWeight', 'bold'));
  grid.setWidget(0, 1, ui.createLabel('Store Name').setStyleAttribute('fontWeight', 'bold'));
  grid.setWidget(0, 2, ui.createLabel('Address').setStyleAttribute('fontWeight', 'bold'));

  // For each entry in restaurantInfo, create a map marker with the address and
  // the style we want. Also add the address info for this restaurant to the
  // grid widget.
  for (var i = 0; i < restaurantInfo.length; i++) {
    restaurantMap.setMarkerStyle(Maps.StaticMap.MarkerSize.MID,
                                 Maps.StaticMap.Color.GREEN,
                                 i + 1);
    restaurantMap.addMarker(restaurantInfo[i][1]);

    grid.setWidget(i + 1, 0, ui.createLabel((i + 1).toString()));
    grid.setWidget(i + 1, 1, ui.createLabel(restaurantInfo[i][0]));
    grid.setWidget(i + 1, 2, ui.createLabel(restaurantInfo[i][1]));
  }

  // Create a Flow Panel widget. We add the map and the grid to this panel.
  // The height needs to be able to accomodate the number of restaurants, so we
  // use a calculation to scale it based on the number of restaurants.
  var panel = ui.createFlowPanel().setSize('500px', 515 + (restaurantInfo.length * 25) + 'px');

  // Get the URL of the restaurant map and use that to create an image and add
  // it to the panel. Next add the grid to the panel.
  panel.add(ui.createImage(restaurantMap.getMapUrl()));
  panel.add(grid);

  // Finally, add the panel widget to our UI instance, and set its height,
  // width, and title.
  ui.add(panel);
  ui.setHeight(515 + (restaurantInfo.length * 25));
  ui.setWidth(500);
  ui.setTitle('Restaurant Locations');

  // Make the UI visible in the spreadsheet.
  SpreadsheetApp.getActiveSpreadsheet().show(ui);
}

/*
 // Logs how long it would take to walk from Times Square to Central Park.
 var directions = Maps.newDirectionFinder()
     .setOrigin('Times Square, New York, NY')
     .setDestination('Central Park, New York, NY')
     .setMode(Maps.DirectionFinder.Mode.WALKING)
     .getDirections();
 Logger.log(directions.routes[0].legs[0].duration.text);
*/

function getDrivingDirections() {
  // Set starting and ending addresses
  var start = '1600 Amphitheatre Pkwy, Mountain View, CA 94043';
  var end = '345 Spear St, San Francisco, CA 94105';

  // These regular expressions will be used to strip out
  // unneeded HTML tags
  var r1 = new RegExp('<b>', 'g');
  var r2 = new RegExp('</b>', 'g');
  var r3 = new RegExp('<div style="font-size:0.9em">', 'g');
  var r4 = new RegExp('</div>', 'g');

  // points is used for storing the points in the step-by-step directions
  var points = [];

  // currentLabel is used for number the steps in the directions
  var currentLabel = 0;

  // This will be the map on which we display the path
  var map = Maps.newStaticMap().setSize(500, 350);

  // Create a new UI Application, which we use to display the map
  var ui = UiApp.createApplication();
  // Create a Flow Panel widget, which we use for the directions text
  var directionsPanel = ui.createFlowPanel();

  // Create a new DirectionFinder with our start and end addresses, and request the directions
  // The response is a JSON object, which contains the directions
  var directions = Maps.newDirectionFinder().setOrigin(start).setDestination(end).getDirections();

  // Much of this code is based on the template referenced in
  // http://googleappsdeveloper.blogspot.com/2010/06/automatically-generate-maps-and.html
  // https://developers.google.com/apps-script/reference/maps/direction-finder#getdirections
  for (var i in directions.routes) {
    for (var j in directions.routes[i].legs) {
      for (var k in directions.routes[i].legs[j].steps) {
        // Parse out the current step in the directions
        var step = directions.routes[i].legs[j].steps[k];

        // Call Maps.decodePolyline() to decode the polyline for
        // this step into an array of latitudes and longitudes
        var path = Maps.decodePolyline(step.polyline.points);
        points = points.concat(path);

        // Pull out the direction information from step.html_instructions
        // Because we only want to display text, we will strip out the
        // HTML tags that are present in the html_instructions
        var text = step.html_instructions;
        text = text.replace(r1, ' ');
        text = text.replace(r2, ' ');
        text = text.replace(r3, ' ');
        text = text.replace(r4, ' ');

        // Add each step in the directions to the directionsPanel
        directionsPanel.add(ui.createLabel((++currentLabel) + ' - ' + text));
      }
    }
  }

  // be conservative and only sample 100 times to create our polyline path
  var lpoints=[];
  if (points.length < 200)
    lpoints = points;
  else {
    var pCount = (points.length / 2);
    var step = parseInt(pCount / 100);
    for (var i = 0; i < 100; ++i) {
      lpoints.push(points[i * step * 2]);
      lpoints.push(points[(i * step * 2) + 1]);
    }
  }

  // make the polyline
  if (lpoints.length > 0) {
    // Maps.encodePolyline turns an array of latitudes and longitudes
    // into an encoded polyline
    var pline = Maps.encodePolyline(lpoints);

    // Once we have the encoded polyline, add that path to the map
    map.addPath(pline);
  }

  // Create a FlowPanel to hold the map
  var panel = ui.createFlowPanel().setSize('500px', '350px');

  // Get the URL of the map and use that to create an image and add
  // it to the panel.
  panel.add(ui.createImage(map.getMapUrl()));

  // Add both the map panel and the directions panel to the UI instance
  ui.add(panel);
  ui.add(directionsPanel);

  // Next set the title, height, and width of the UI instance
  ui.setTitle('Driving Directions');
  ui.setHeight(525);
  ui.setWidth(500);

  // Finally, display the UI within the spreadsheet
  SpreadsheetApp.getActiveSpreadsheet().show(ui);
}

function analyzeLocations() {
  // Select the sheet named 'geocoder and elevation'
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('geocoder and elevation');

  // Store the address data in an array called
  // locationInfo. This is the data in cells A2:A20
  var locationInfo = sheet.getRange(2, 1, sheet.getLastRow() - 1, 1).getValues();

  // Set up some values to use for comparisons.
  // latitudes run from -90 to 90, so we start with a max of -90 for comparison
  var maxLatitude = -90;
  var indexOfMaxLatitude = 0;

  // Set the starting max elevation to 0, or sea level
  var maxElevation = 0;
  var indexOfMaxElevation = 0;

  // geoResults will hold the JSON results array that we get when calling geocode()
  var geoResults;

  // elevationResults will hold the results object that we get when calling sampleLocation()
  var elevationResults;

  // lat and lng will temporarily hold the latitude and longitude of each
  // address
  var lat, lng;

  for (var i = 0; i < locationInfo.length; i++) {
    // Get the latitude and longitude for an address. For more details on
    // the JSON results array, geoResults, see
    // http://code.google.com/apis/maps/documentation/geocoding/#Results
    geoResults = Maps.newGeocoder().geocode(locationInfo[i]);

    // Get the latitude and longitude
    lat = geoResults.results[0].geometry.location.lat;
    lng = geoResults.results[0].geometry.location.lng;

    // Use the latitude and longitude to call sampleLocation and get the
    // elevation. For more details on the JSON-formatted results object,
    // elevationResults, see
    // http://code.google.com/apis/maps/documentation/elevation/#ElevationResponses
    elevationResults = Maps.newElevationSampler().sampleLocation(parseFloat(lat), parseFloat(lng));

    // Check to see if the current latitude is greater than our max latitude
    // so far. If so, set maxLatitude and indexOfMaxLatitude
    if (lat > maxLatitude) {
      maxLatitude = lat;
      indexOfMaxLatitude = i;
    }

    // Check if elevationResults has a good status and also if the current
    // elevation is greater than the max elevation so far. If so, set
    // maxElevation and indexOfMaxElevation
    if (elevationResults.status == 'OK' && elevationResults.results[0].elevation > maxElevation) {
      maxElevation = elevationResults.results[0].elevation;
      indexOfMaxElevation = i;
    }
  }

  // User Browser.msgBox as a simple way to display the info about highest
  // elevation and northernmost office.
  Browser.msgBox('The US Google office with the highest elevation is: ' + locationInfo[indexOfMaxElevation] +
                 '. The northernmost US Google office is: ' + locationInfo[indexOfMaxLatitude]);
}

