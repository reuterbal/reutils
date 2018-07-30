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

## passwd2ldif

Convert given `passwd` and `group` file into an LDIF file that can be used
to initialize an LDAP database with these values.

This is useful if you move your user authentication from NIS to LDAP.

It extracts `uid`, `uidNumber`, `gidNumber`, `displayName`, `homeDirectory`,
and `loginShell` from the `passwd` file and writes an LDIF-entry with 
`$variable` replaced by these extracted values:
```LDIF
dn: cn=$displayName,ou=people,dc=sub,dc=domain,dc=de
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
displayName: $displayName
uidNumber: $uidNumber
loginShell: $loginShell
homeDirectory: $homeDirectory
cn: $displayName
gidNumber: $gidNumber
sn: $sn
givenName: $givenName
uid: $uid
```
`$sn` and `$givenName` are extracted from `$displayName` by splitting after
the first white space.

Additionally, it extracts `cn`, `gidNumber`, and `uids` from the `group` file
and creates LDIF-entries:
```LDIF
dn: cn=$cn,ou=groups,dc=sub,dc=domain,dc=de
objectClass: groupOfNames
objectClass: posixGroup
cn: $cn
gidNumber: $gidNumber
member: cn=...
member: cn=...
...
```
where the members are extracted from `$uids` and filled with the values 
derived from the `passwd` file.
