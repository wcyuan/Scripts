/*
  Deep copy a folder on google drive.

Started with http://techawakening.org/?p=2846
(http://webapps.stackexchange.com/questions/40164/can-i-duplicate-a-folder-in-google-drive)
But that version:
 - adds "_copy" to the name of all folders
 - doesn't properly handle all cases involving sub-folders and sub-files with the same name.
 - is fairly convoluted
 - uses the deprecated "script properties"
   https://developers.google.com/apps-script/reference/properties/script-properties

So I took the general framework (running the script within a spreadsheet), but otherwise
completely rewrote it.

--- The new folder appears at the top level of your google drive
--- The max execution time is 6 minutes: https://developers.google.com/apps-script/guides/services/quotas
*/

// ---------------------------------------------------------------------------------------- //

// https://developers.google.com/apps-script/reference/spreadsheet/spreadsheet#toast(String,String,Number)
// if timeout is null, default to 5 seconds
// if timeout is negative, stay forever
function toast(msg, title, timeout) {
  Logger.log(msg);
  SpreadsheetApp.getActiveSpreadsheet().toast(msg, title, timeout);
}

// ---------------------------------------------------------------------------------------- //

function onOpen() {
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    var menuEntries = [{
            name: "1. Authorize",
            functionName: "authorize"
        }, {
            name: "2. Make a Copy",
            functionName: "copy_all"
        }

    ];
    spreadsheet.addMenu("GDrive: Copy Folder", menuEntries);
    toast("Select GDrive: Copy Folder-> Authorize. This is an One Time Action.", "Get Started", -1);
}

// ---------------------------------------------------------------------------------------- //

function authorize() {
    toast("Enter Folder ID and  Select GDrive: Copy Folder->  Make a Copy", "", -1);
}

// ---------------------------------------------------------------------------------------- //

function copy_all() {
  var folder_to_copy = get_folder_to_copy();
  if (folder_to_copy !== null) {
    toast("Found folder to copy: " + folder_to_copy.getName(), "Copying...", -1);
    deep_copy_folder(folder_to_copy, DriveApp.getRootFolder());
    toast("Finished copying: " + folder_to_copy.getName(), "Finished.", -1);
  }
}

function get_folder_to_copy() {
  var folder_id = SpreadsheetApp.getActiveSheet().getRange("B5").getValue().toString().trim();
  try {
    return DriveApp.getFolderById(folder_id);
  } catch (e) {
    Browser.msgBox("Error", "Sorry, Error Occured: " + e.toString(), Browser.Buttons.OK);
    toast("Error Occurred :( Please make sure you Entered Folder ID in B5 Cell.", "Oops!", -1);
    return null;
  }
}

function deep_copy_folder(orig_folder, target_parent) {
  var new_folder = target_parent.createFolder(orig_folder.getName());
  var orig_files = orig_folder.getFiles();
  while (orig_files.hasNext()) {
    var orig_file = orig_files.next();
    toast(orig_file.getName(), "Copying...", -1);
    orig_file.makeCopy(orig_file.getName(), new_folder);
  }
  var orig_subfolders = orig_folder.getFolders();
  while (orig_subfolders.hasNext()) {
    var orig_subfolder = orig_subfolders.next();
    toast(orig_subfolder.getName(), "Copying...", -1);
    deep_copy_folder(orig_subfolder, new_folder);
  }
}

// ---------------------------------------------------------------------------------------- //
