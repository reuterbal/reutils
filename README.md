# reutils
Small utilities created by me. 

## archive2svn

Convert one or multiple series of archives into an SVN repository.

Useful if you have some archive files (.tar.gz or similar) that 
represent, e.g., old versions of your code at different times.

Simply fill in the repository url and pattern list in the beginning of the 
file to match your needs and run the script.
It will automatically build a list of all archives that match your pattern
list and sort them by date (either given in the filename or by taking the
modification date of the latest item in the archive).
Each archive will appear as a new revision in the SVN repository with the
commit date according to the archive date.

