//
// This is a Google Sheets App-script that I used in a TEALS
// grading sheet.  
// 
//

// ------------------------------------------------------
// onEdit
//
// This function is used to keep track of the "Last Graded" date for each student.
//
// onEdit is a special function that is called whenever the Google Sheet is edited.
// This implementation requires that the sheet be called "All Students".
// Then, any time an edit happens to any column after the first 5
// (the first 5 columns are reserved for the rubic)
// it notes the current date in the 6th row.
// It knows that students actually get 2 rows (one for points, one for comments)
// so any edit to an even numbered column (which contains comments) actually updates
// the "last graded" row of the previous column (which contains the points).
//
// Useful reference websites:
//
// http://webapps.stackexchange.com/questions/33372/how-can-i-automatically-set-last-updated-cell-in-row-google-docs-spreadsheets
// https://developers.google.com/apps-script/guides/triggers/events#google_sheets_events
// https://developers.google.com/apps-script/guides/triggers/#onedit
// https://developers.google.com/apps-script/reference/spreadsheet/sheet
// https://developers.google.com/apps-script/reference/spreadsheet/range
// https://developers.google.com/apps-script/reference/base/logger
function onEdit(e) {
  var s = SpreadsheetApp.getActiveSheet();
  if (s.getName() !== "All Students") {
    //Logger.log("Skipping edit in sheet: " + s.getName());
    return;
  };
  var c = e.range;
  Logger.log(e);
  if (c.getRow() == 6) {
    //Logger.log("Skipping edit in row 6");
    return;
  };
  if (c.getColumn() < 5) {
    //Logger.log("Skipping edit in column < 5");
    return;
  }
  var col = c.getColumn();
  if (col % 2 == 0) {
    col = col - 1;
  }
  var time = new Date();
  time = Utilities.formatDate(time, "EST", "YYYY-MM-dd");
  // The user's email is generaly blank, I guess because of lack of permissions.
  //var grader = e.user.getEmail();
  s.getRange(6, col).setValue(time);
}


//
// This is a Google Sheets App-script add-on which duplicates the current sheet
// many times, to a hard-coded set of names.
//
// To install it, in a Google Sheet, go to the Tools menu and choose "Script Editor..."
// Then just copy and paste this there.  Then reload the sheet.  A new menu should appear
// with this function in it.
//

var COPIES = [
  'name1',
  'name2'
];

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
    ui.alert('Press OK to Continue.');
    copySheet_(spreadsheet, sheet, filtered);
  } else {
    // User clicked "No" or X in the title bar.
    ui.alert('Press OK to Cancel.');
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
    var new_sheet = sheet.copyTo(spreadsheet);
    new_sheet.setName(name);
    // This also sets the value of cell D1 to the name of the sheet
    // Note that getRange is 1-indexed.  Column #1 = Column "D".
    new_sheet.getRange(1, 4).setValue(name);
  }
}
