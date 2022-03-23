# Usage of the LDML_entry.ods spreadsheet

GitHub repository: github.com/silnrsi/sldrtools

The LDML_entry.ods file (sldrtools/data) is a LibreOffice calc spreadsheet designed for entry of LDML data.

## Initial setup

(1) with LibreOffice Calc

- Open LDML_entry.ods
- Save with a name that represents the locale, for example: "LDML_entry_xyz-Latn.ods"

(2) with Microsoft Excel

- Open LDML_entry.ods
- Use File, SaveAs, choose .xlsx format, and assign a name that represents the locale, for example, "LDML_entry_xyz-Latn.xlsx".

(3) with Google sheets

- Open a blank Google sheet
- Select Import function (type Alt+/, then start typing "import", and select "import" from list)
- Select Upload
- Either drag the LDML_entry.ods file to the indicated location, or else click "Select a file from your device" and navigate to LDML_entry.ods
- Select "Replace spreadsheet" (to replace the blank Google sheet with the one you just created from the LDML_entry.ods file) and "Import data"
- Give a title to the spreadsheet that represents the locale (perhaps using Ctrl+Shift+F to show the menus and the spreadsheet name field), for example, "LDML_entry_xyz-Latn".

For any of these options

- You may use the "Notes" sheet in any way you wish to discuss options, track decisions, etc.
- Be sure to fill in the Contributor information, and the Language, Script and Region codes.

## Generation of LDML

The sheetldml Python script (sldrtools/scripts) can be used to create an LDML file

- If necessary, convert the data back to the .ods file format
- From the command line: python sheetldml LDML_entry_xyz-Latn.ods xyz.xml

It is also possible to use a TSV (tab separted value) file

- From the command line: python sheetldml -t LDML_entry_xyz-Latn.tsv xyz.xml

## Initialization of spreadsheet
The sheetldml script can also be used to read an existing LDML file and a blank .ods template file
to create an .ods file with the data from the existing LDML file filled in.

- From the command line: python sheetldml.py -o LDML_entry_xyz-Latn.ods LDML_entry.ods xyz.ldml

(where LDML_entry.ods is the blank template file, xyz.ldml is the existing LDML file 
and LDML_entry_xyz-Latn.ods is the spreadsheet initialized from the LDML file).
