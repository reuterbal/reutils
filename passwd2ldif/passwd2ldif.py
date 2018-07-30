#!/usr/bin/env python3
# Created by balthasar.reuter at fau.de, 2016

# Convert /etc/passwd to an LDIF file

### Configuration ###

ldif_file = 'passwd_export.ldif'
ldap_base = 'dc=sub,dc=domain,dc=de'

passwd_file = 'passwd'

passwd_fields = ( 
                  'uid',
                  'password',
                  'uidNumber',
                  'gidNumber',
                  'displayName',
                  'homeDirectory',
                  'loginShell'
                )

passwd_field_ignore = ( 'password', )

uid_ignore =  (
                'testuser',
              )

uidNumber_min = 1200
uidNumber_max = 65533

user_base = 'ou=people,' + ldap_base
user_objectClass = ( 'inetOrgPerson', 'posixAccount', 'shadowAccount' )

group_file = 'group'

group_fields =  (
                  'cn',
                  'password',
                  'gidNumber',
                  'uids'
                )

group_field_ignore = ( 'password', )

group_ignore = ( 'testuser', )

gidNumber_min = 1200
gidNumber_max = 65533

group_base = 'ou=groups,' + ldap_base
group_objectClass = [ 'groupOfNames', 'posixGroup' ]

default_group = 'user'

ldif_header = '''
dn: dc=sub,dc=domain,dc=de
dc: sub
o: sub.domain.de
objectclass: dcObject
objectclass: organization

dn: cn=root,dc=sub,dc=domain,dc=de
cn: root
description: rootdn
objectclass: organizationalRole
objectclass: top

dn: ou=groups,dc=sub,dc=domain,dc=de
ou: groups
objectclass: organizationalUnit
objectclass: top

dn: ou=people,dc=sub,dc=domain,dc=de
ou: people
objectclass: organizationalUnit
objectclass: top

dn: cn=organizational,ou=groups,dc=sub,dc=domain,dc=de
objectClass: groupOfNames
objectClass: posixGroup
gidNumber: 1100
cn: organizational
member: cn=NSLCD,ou=people,dc=sub,dc=domain,dc=de

dn: cn=NSLCD,ou=people,dc=sub,dc=domain,dc=de
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
displayName: NSLCD
uidNumber: 1101
loginShell: /bin/false
homeDirectory: /nonexistent
cn: NSLCD
gidNumber: 1100
sn: NSLCD
givenName: NSLCD
uid: nslcd

'''

### Functions ###

def convert_user(input_file, fields, field_ignore, ignore=[], uid_min=0, uid_max=65533):
  """Converts passwd file into a list of dictionaries"""
  users = []
  f = open(input_file, 'r')

  # Convert each line 
  for line in f:
    # Extract line from passwd and split it into a list
    line = line.strip(' \n')
    user_line = line.split(':')

    # Check for ignored user or uid
    if user_line[0] in ignore:
      continue
    elif int(user_line[2]) < uid_min:
      continue
    elif int(user_line[2]) > uid_max:
      continue

    # Convert to a dictionary
    user_line[4] = user_line[4].split(',')[0]
    user = dict(zip(fields, user_line))

    # Remove ignored fields
    for k in field_ignore:
      user.pop(k, None)

    # Extract name
    name = user['displayName'].split('(')[0]
    user['cn'] = name
    name = name.split()
    user['givenName'] = ' '.join(name[0:-1])
    user['sn'] = name[-1]

    users.append(user)

  f.close()
  return users

def user_2_ldif(users, base, object_class):
  """Converts list of dictionaries into LDIF formatted string"""
  oc_string = ''
  for oc in object_class:
    oc_string += 'objectClass: ' + oc + '\n'

  ldif = ''
  for user in users:
    ldif += 'dn: cn=' + user['cn'].strip() + ',' + base + '\n'
    ldif += oc_string
    for k, v in user.items():
      ldif += k + ': ' + v.strip() + '\n'
    ldif += '\n'
  return ldif

def convert_group(input_file, fields, field_ignore, ignore=[], gid_min=0, gid_max=65533):
  """Converts group file into a list of dictionaries"""
  groups = []
  f = open(input_file, 'r')

  # Convert each line 
  for line in f:
    # Extract line from passwd and split it into a list
    line = line.strip(' \n')
    group_line = line.split(':')

    # Check for ignored user or uid
    if group_line[0] in ignore:
      continue
    elif int(group_line[2]) < gid_min:
      continue
    elif int(group_line[2]) > gid_max:
      continue

    # Convert to a dictionary
    group = dict(zip(fields, group_line))

    # Remove ignored fields
    for k in field_ignore:
      group.pop(k, None)

    # Convert string of members to list
    if len(group['uids']) > 0:
      group['uids'] = group['uids'].split(',')

    groups.append(group)

  f.close()
  return groups

def group_2_ldif(groups, users, group_base, user_base, object_class, default_group):
  """Converts list of dictionaries into LDIF formatted string"""
  oc_string = ''
  for oc in object_class:
    oc_string += 'objectClass: ' + oc + '\n'

  ldif = ''
  for group in groups:
    ldif += 'dn: cn=' + group['cn'].strip() + ',' + group_base + '\n'
    ldif += oc_string

    member = ''
    if 'uids' in group:
      if group['cn'] == default_group:
        for u in users:
          member += 'member: cn=' + u['cn'].strip() + ',' + user_base + '\n'
      else:
        for uid in group['uids']:
          matching_users = tuple(u for u in users if u['uid'] == uid)
          for u in matching_users:
            member += 'member: cn=' + u['cn'].strip() + ',' + user_base + '\n'
      if len(member) == 0:
        print('Warning: Group "' + group['cn'] + '" has no members!')
      del group['uids']

    for k, v in group.items():
      ldif += k + ': ' + v.strip() + '\n'

    ldif += member
    ldif += '\n'
  return ldif

def main():
  users = convert_user(passwd_file, passwd_fields, passwd_field_ignore, uid_ignore, uidNumber_min, uidNumber_max)
  groups = convert_group(group_file, group_fields, group_field_ignore, group_ignore, gidNumber_min, gidNumber_max)
  
  f = open(ldif_file, 'w')
  f.write(ldif_header)
  f.write(user_2_ldif(users, user_base, user_objectClass))
  f.write(group_2_ldif(groups, users, group_base, user_base, group_objectClass, default_group))
  f.close()

  return 0

if __name__ == "__main__":
  exit(main())
