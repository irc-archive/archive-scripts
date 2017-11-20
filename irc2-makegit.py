#!/usr/bin/env python3
# ircd git generation from archive files
# like irc2.1.1.tar

# code
import datetime
import os
import shutil
import subprocess
import tarfile

# settings
history_files_dir = 'history_files'
git_dir = 'repo'

# misc info for time grabbing
year_lookup = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12',
}

# files/folders
if not os.path.exists(git_dir):
    os.makedirs(git_dir)

ircd_archive_files = [f for f in os.listdir(os.path.join(os.curdir, history_files_dir)) if f.startswith('irc2') and ('tgz' in f or 'tar' in f)]

# sort versions
versions = {}
for name in ircd_archive_files:
    ver = name.lstrip('irc').replace('.tgz', '').replace('.tar.gz', '').replace('.tar.Z', '').replace('.tar', '')
    if '+' in ver or 'patched' in ver or 'jp' in ver or 'bu' in ver:
        continue
    versions[ver] = os.path.join(history_files_dir, name)

# git
subprocess.run(['git', 'init'], cwd=git_dir)
subprocess.run(['git', 'config', 'user.name', 'Jarkko Oikarinen'], cwd=git_dir)
subprocess.run(['git', 'config', 'user.email', 'jto@tolsun.oulu.fi'], cwd=git_dir)
git_env = os.environ.copy()


# sort the dodgy, weird, mental version numbers of irc2...
def sort_irc2_version_numbers(numbers):
    # split version numbers up
    split_numbers = []

    for ver in numbers:
        cache = []
        buffer = ''
        is_number = True

        for char in ver:
            if char == '.' and buffer:
                if is_number:
                    cache.append(int(buffer))
                else:
                    cache.append(buffer)
                buffer = ''
            elif char.isalpha():
                if buffer == '':
                    ... # fall-through
                elif is_number:
                    cache.append(int(buffer))
                    if len(cache) < 3:
                        cache.append(0)
                    buffer = ''
                else:
                    ... # fall-through
                is_number = False
                buffer += char
            elif char.isdigit():
                if buffer == '':
                    ... # fall-through
                elif not is_number:
                    cache.append(buffer)
                    buffer = ''
                else:
                    ... # fall-through
                is_number = True
                buffer += char
            else:
                print("GOD DAMNIT WHAT IS THIS JUNK:", ver, char)
        
        if is_number and buffer:
            cache.append(int(buffer))
        elif buffer:
            cache.append(buffer)
        
        if len(cache) < 3:
            cache.append(0)
        if len(cache) < 4:
            cache.append('c') # so release get sorted after alpha ('a') and beta ('b') releases, but before post-release patch ('p') releases. please kill me.
        if len(cache) < 5:
            cache.append(0)
        
        split_numbers.append([cache, ver])
    
    sorted_vers = []
    for ver in sorted(split_numbers):
        sorted_vers.append(ver[1])

    return sorted_vers


# extract
sorted_versions = sort_irc2_version_numbers(list(versions.keys()))
last_recorded_changelog_date = ''
for version in sorted_versions:
    filename = versions[version]

    gzfile = tarfile.open(filename, 'r')
    gzfile.extractall(git_dir)

    ons_folders = [f for f in os.listdir(git_dir) if f.lower().startswith('irc')]
    extracted_folder = os.path.join(git_dir, ons_folders[0])

    extracted_file_list = os.listdir(extracted_folder)

    # get time from file entries
    time_to_use = ''
    last_modified_time = 0
    for filename in extracted_file_list:
        # only get time if it's a real file, not a symlink
        original_filename = os.path.join(extracted_folder, filename)
        if os.path.isfile(original_filename):
            modified_time = float(os.path.getmtime(original_filename))
            if modified_time > last_modified_time:
                last_modified_time = modified_time

    for filename in extracted_file_list:
        original_filename = os.path.join(extracted_folder, filename)
        new_filename = os.path.join(git_dir, filename)

        shutil.move(original_filename, new_filename)

    # get last modified time from changelog if it exists - more accurate
    changelog_path = os.path.join(git_dir, 'doc/ChangeLog')
    if os.path.exists(changelog_path):
        changelog = open(changelog_path, 'r', encoding='latin1').read()

        # get date from latest changelog entry
        import re
        exact_time_re = re.compile('(?:([A-Z][a-z]{2}) ([0-9]+) ([0-9:]+) ([0-9]{4})|([0-9]{4})-([0-9]{2})-([0-9]{2}))')
        matches = exact_time_re.findall(changelog)
        if 0 < len(matches):
            year = ''
            month = ''
            day = ''
            time = '09:00:00'

            match = matches[0]

            if match[-1] == '':
                year = match[3]
                month = year_lookup[match[0]]
                day = match[1]
                time = match[2]
            else:
                year = match[4]
                month = match[5]
                day = match[6]
            
            new_changelog_date = year + '-' + month + '-' + day + ' ' + time
            if last_recorded_changelog_date == new_changelog_date:
                time_to_use = datetime.datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_to_use = new_changelog_date

            last_recorded_changelog_date = new_changelog_date
    else:
        time_to_use = datetime.datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')

    shutil.rmtree(extracted_folder)

    git_env['GIT_AUTHOR_DATE'] = str(time_to_use)
    git_env['GIT_COMMITTER_DATE'] = str(time_to_use)
    subprocess.run(['git', 'add', '.'], cwd=git_dir)  # add additions and deletions
    subprocess.run(['git', 'commit', '-m', 'irc{}'.format(version)], cwd=git_dir, env=git_env)

    for filename in extracted_file_list:
        new_filename = os.path.join(git_dir, filename)
        if os.path.isdir(new_filename):
            shutil.rmtree(new_filename)
        else:
            os.remove(new_filename)

    print('Extracted and committed irc{}'.format(version))
