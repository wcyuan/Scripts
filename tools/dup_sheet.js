//
// This is a Google Sheets App-script add-on which duplicates the current sheet
// many times, to a hard-coded set of names.
//
// To install it, in a Google Sheet, go to the Tools menu and choose "Script Editor..."
// Then just copy and paste this there.  Then reload the sheet.  A new menu should appear
// with this function in it.
//

var COPIES = [
  'First',
  'Second',
  'Third'];

function onOpen() {
  var spreadsheet = SpreadsheetApp.getActive();
  var menuItems = [
    {name: 'Copy sheet to all names...', functionName: 'confirmCopySheet_'}
  ];
  spreadsheet.addMenu('Custom-Functions', menuItems);
}

function confirmCopySheet_() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getActiveSheet();
  var filtered = getFiltered_(sheet, COPIES);
  var to_delete = toDelete_(spreadsheet, filtered);
  var ui = SpreadsheetApp.getUi(); // Same variations.
  var result = ui.alert(
    'Please confirm.  Copying sheet ' + sheet.getName() + ' to sheets: ' +
    filtered + '.  The following existing sheets need to be deleted: ' +
      to_delete + '.  Are you sure you want to continue?',
        ui.ButtonSet.YES_NO);

  // Process the user's response.
  if (result == ui.Button.YES) {
    // User clicked "Yes".
    ui.alert('Continuing...');
    copySheet_(spreadsheet, sheet, filtered);
  } else {
    // User clicked "No" or X in the title bar.
    ui.alert('Canceling.');
  }
}

function getFiltered_(sheet, names) {
  var filtered = [];
  for (var ii = 0; ii < names.length; ii++) {
    if (sheet.getName() !== names[ii]) {
      filtered.push(names[ii]);
    }
  }
  return filtered;
}

function toDelete_(spreadsheet, names) {
  var filtered = [];
  for (var ii = 0; ii < names.length; ii++) {
    var existing = spreadsheet.getSheetByName(names[ii]);
    if (existing !== null) {
      filtered.push(names[ii]);
    }
  }
  return filtered;
}

function copySheet_(spreadsheet, sheet, names) {
  Logger.log("Copying sheet " + sheet.getName() + " to names: " + names);
  for (index = 0; index < names.length; index++) {
    var name = names[index];
    Logger.log("Copy to sheet named: " + name);
    if (sheet.getName() === name) {
      Logger.log("Skipping active sheet: " + name);
      continue;
    };
    var existing = spreadsheet.getSheetByName(name);
    if (existing !== null) {
      Logger.log("Deleting existing sheet: " + name + " -> " + existing);
      spreadsheet.deleteSheet(existing);
    } else {
      Logger.log("No exising sheet for: " + name);
    };
    sheet.copyTo(spreadsheet).setName(name);
  }
}
