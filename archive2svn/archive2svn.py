#!/usr/bin/env python
# Created by balthasar.reuter@fau.de, 2015

# Convert one or multiple series of archives into an SVN repository

# Note: To allow for the correct commit date, the pre-revprop-change hook must be 
#       enabled for the repository, e.g., by calling
#       printf '#!/bin/bash\nexit 0' > /path/to/your/repository/hooks/pre-revprop-change && \
#          chmod +x /home/reuter/utbest-archiv/hooks/pre-revprop-change
#       (see http://svnbook.red-bean.com/en/1.7/svn.ref.reposhooks.pre-revprop-change.html)

import os
import fnmatch
import re
import glob
import subprocess
from datetime import date, datetime
import tarfile

#####################
### Configuration ###
#####################

# Pattern in 'svn status' to identify missing files
svn_del_pattern = "^\!"

# Pattern in 'svn status' to identify new files
svn_new_pattern = "^\?"

# Path to svn repository
repository_url = "file:///home/reuter/utbest-archiv"

# Path to svn working copy
working_copy = "tmp-working-copy"

# List of patterns by which archives are to be identified
# Each entry consists of the following tuple: (subdir, name-pattern, date-pattern)
# - subdir:       The subdirectory in the working copy into which the archive should be extracted
# - name-pattern: A pattern by which the filenames of the archives can be identified
# - date-pattern: A pattern by which the date can be retrieved from the file name. If empty,
#                 the date ist determined automatically as the latest modification date of the
#                 files in the archive
pattern_list = [ ("ldg1d",                         "ldg1d_??-??-??.tar.gz",                         "ldg1d_%y-%m-%d.tar.gz"                         ),
                 ("ldg2d",                         "ldg2d_??-??-??.tar.gz",                         "ldg2d_%y-%m-%d.tar.gz"                         ),
                 ("ldg_ns",                        "ldg_ns_????-??-??.tar.gz",                      "ldg_ns_%Y-%m-%d.tar.gz"                        ),
                 ("ldg_ns_coupled",                "ldg_ns_coupled_????-??-??.tar.gz",              "ldg_ns_coupled_%Y-%m-%d.tar.gz"                ),
                 ("ldg_ns_coupled_test",           "ldg_ns_coupled_test_????-??-??.tar.gz",         "ldg_ns_coupled_test_%Y-%m-%d.tar.gz"           ),
                 ("ldg_ns_laplace",                "ldg_ns_laplace_????-??-??.tar.gz",              "ldg_ns_laplace_%Y-%m-%d.tar.gz"                ),
                 ("ldg_ns_ldg",                    "ldg_ns_ldg_????-??-??.tar.gz",                  "ldg_ns_ldg_%Y-%m-%d.tar.gz"                    ),
                 ("ldg_utbest",                    "ldg_utbest_??-??-??.tar.gz",                    "ldg_utbest_%y-%m-%d.tar.gz"                    ),
                 ("utbest_2d",                     "utbest_2d_??-??-??.tar.gz",                     "utbest_2d_%y-%m-%d.tar.gz"                     ),
                 ("utbest_3d",                     "utbest_3d_??-??-??.tar.gz",                     "utbest_3d_%y-%m-%d.tar.gz"                     ),
                 ("utbest_3d_nonworking",          "utbest_3d_??-??-??_nonworking.tar.gz",          "utbest_3d_%y-%m-%d_nonworking.tar.gz"          ),
                 ("utbest_3d_analyzed",            "utbest_3d_analyzed_??-??-??.tar.gz",            "utbest_3d_analyzed_%y-%m-%d.tar.gz"            ),
                 ("utbest_3d_density",             "utbest_3d_density.tar.gz",                      ""                                              ),
                 ("utbest_3d_tmp",                 "utbest_3d_tmp[0-9]*.tar.gz",                    ""                                              ),
                 ("utbest_3d_tracer",              "utbest_3d_tracer_??-??-??.tar.gz",              "utbest_3d_tracer_%y-%m-%d.tar.gz"              ),
                 ("utbest_3d_tracer_k-epsilon",    "utbest_3d_tracer_k-epsilon_??-??-??.tar.gz",    "utbest_3d_tracer_k-epsilon_%y-%m-%d.tar.gz"    ),
                 ("utbest_3d_turbulence",          "utbest_3d_turbulence_??-??-??.tar.gz",          "utbest_3d_turbulence_%y-%m-%d.tar.gz"          ),
                 ("utbest_3d_turbulence_macro",    "utbest_3d_turbulence_??-??-??_macro.tar.gz",    "utbest_3d_turbulence_%y-%m-%d_macro.tar.gz"    ),
                 ("utbest_3d_turbulence_parallel", "utbest_3d_turbulence_parallel_??-??-??.tar.gz", "utbest_3d_turbulence_parallel_%y-%m-%d.tar.gz" ),
                 ("work_navier_stokes_2d",         "work_navier_stokes_2d.tar.gz",                  ""                                              ) ]


###############
### Classes ###
###############

class Archive2SvnException(Exception):
  pass

#################
### Functions ###
#################

def tardate(filename):
  if tarfile.is_tarfile(filename):
    tar = tarfile.open(filename)
    times = [member.mtime for member in tar.getmembers()]
    mtime = max(times)
    tar.close()
    return mtime
  else:
    raise Archive2SvnException("Not a supported tar-file: '{}'".format(filename))


def untar(filename, target):
  if tarfile.is_tarfile(filename):
    tar = tarfile.open(filename)
    tar.extractall(target)
    tar.close()
  else:
    raise Archive2SvnException("Not a supported tar-file: '{}'".format(filename))


def build_archive_list(pattern_list, target_dir):
  glob_file_list = []

  for pattern in pattern_list:
    # Extract patterns
    subdir = pattern[0]
    file_pattern = pattern[1]
    date_pattern = pattern[2]

    # Build list of files
    if len(date_pattern) > 0:
      file_list = [ (datetime.strptime(file_name, date_pattern).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), file_name, subdir)
                      for file_name in os.listdir(target_dir) if fnmatch.fnmatch(file_name, file_pattern) ]
    else:
      file_list = [ (date.fromtimestamp(tardate(file_name)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), file_name, subdir)
                      for file_name in os.listdir(target_dir) if fnmatch.fnmatch(file_name, file_pattern) ]

    assert len(file_list) > 0

    # Append files to global list
    glob_file_list.extend(file_list)

  # Sort the global list by date and return it
  glob_file_list.sort(key=lambda x: x[0])
  return glob_file_list


def add_archive(archive, datestr, target_dir):
  print datestr + ": Archive '" + archive + "' into '" + target_dir + "'"

  # Delete all files in the working copy
  if os.path.isdir(target_dir):
    subprocess.call(["rm", "-rf", target_dir])

  # Extract archive
  untar(archive, target_dir)

  # Save current working directory
  cwd = os.getcwd()

  # Enter working copy
  os.chdir(target_dir)

  # Obtain svn status
  status = subprocess.check_output(["svn", "st"]).split('\n')

  # Determine missing and new files
  del_files = [ s[1:].strip() for s in status if re.match(svn_del_pattern, s) ]
  new_files = [ s[1:].strip() for s in status if re.match(svn_new_pattern, s) ]

  print "{} new files and {} files to be deleted".format(len(new_files), len(del_files))

  # Update working copy to restore missing files
  assert subprocess.call(["svn", "up"]) == 0

  # Remove missing files from repository
  if len(del_files) > 0:
    cmd = ["svn", "rm"]
    cmd.extend(del_files)
    subprocess.call(cmd)

  # Add new files to repository
  if len(new_files) > 0:
    cmd = ["svn", "add"]
    cmd.extend(new_files)
    subprocess.call(cmd)

  # Commit changes with archive name as commit message
  subprocess.call(["svn", "ci", "-m", "Content of archive " + archive])

  # Modify commit date to match archive date
  if len(datestr) > 0:
    subprocess.call(["svn", "propset", "svn:date", datestr, 
                     "--revprop", "-r", "HEAD"])

  # Update working copy and assert current state
  assert subprocess.call(["svn", "up"]) == 0
  assert len(subprocess.check_output(["svn", "st"])) == 0

  # Change back to original directory
  os.chdir(cwd)

def main():
  # Save current working directory
  cwd = os.getcwd()

  # Checkout working copy
  assert "Checked out revision" in subprocess.check_output(["svn", "co", repository_url, working_copy])

  # Build global file list
  file_list = build_archive_list(pattern_list, cwd)

  # Treat each archive file
  for entry in file_list:
    add_archive(entry[1], entry[0], working_copy + "/" + entry[2])

  print "Added {} new revisions.".format(len(file_list))

  return 0

if __name__ == "__main__":
  exit(main())

# # Checkout working copy
# assert "Checked out revision" in subprocess.check_output(["svn", "co", repository_url, working_copy])

# # Build list of archive files
# file_list = glob.glob(file_pattern)
# file_list.sort()
# print "Found {} archive files.".format(len(file_list))

# for archive in file_list:
#   # Determine date of archive
#   if len(date_pattern) > 0:
#     datestr = datetime.strptime(archive, date_pattern).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
#     print "Archive {} from {}".format(archive, datestr)
#   else:
#     datestr = date.fromtimestamp(tardate(archive)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
#     print "Archive {} from {}".format(archive, datestr)

#   break


#   # Delete all files in the working copy
#   assert os.path.isdir(working_copy)
#   subprocess.call(["rm", "-rf", working_copy + "/*"])

#   # Extract archive
#   untar(archive, working_copy)

#   # Enter working directory
#   os.chdir(working_copy)

#   # Obtain svn status
#   status = subprocess.check_output(["svn", "st"]).split('\n')

#   # Determine missing and new files
#   del_files = [ s[1:].strip() for s in status if re.match(svn_del_pattern, s) ]
#   new_files = [ s[1:].strip() for s in status if re.match(svn_new_pattern, s) ]

#   print "{} new files and {} files to be deleted".format(len(new_files), len(del_files))

#   # Update working copy to restore missing files
#   assert subprocess.call(["svn", "up"]) == 0

#   # Remove missing files from repository
#   if len(del_files) > 0:
#     cmd = ["svn", "rm"]
#     cmd.extend(del_files)
#     subprocess.call(cmd)

#   # Add new files to repository
#   if len(new_files) > 0:
#     cmd = ["svn", "add"]
#     cmd.extend(new_files)
#     subprocess.call(cmd)

#   # Commit changes with archive name as commit message
#   subprocess.call(["svn", "ci", "-m", "Content of archive " + archive])

#   # Modify commit date to match archive date
#   if len(date_pattern) > 0:
#     subprocess.call(["svn", "propset", "svn:date", datestr, 
#                      "--revprop", "-r", "HEAD"])

#   # Update working copy and assert current state
#   assert subprocess.call(["svn", "up"]) == 0
#   assert len(subprocess.check_output(["svn", "st"])) == 0

#   # Change back to original directory
#   os.chdir(cwd)

# print "Added {} new revisions.".format(len(file_list))