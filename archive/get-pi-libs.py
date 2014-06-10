# Copyright (C) 2014 Regents of the University of California.
# Author: Spencer Sutterlin <ssutterlin1@ucla.edu>
# 
# This file is part of ndn-pi (Named Data Networking - Pi).
#
# ndn-pi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

import os
import subprocess
import shutil

# TODO: check for these libs to be installed first
lib_names = ["libboost_date_time.so", "libboost_filesystem.so", "libboost_iostreams.so", "libboost_program_options.so", "libboost_regex.so", "libboost_system.so", "libboost_chrono.so", "libboost_thread.so", "libssl.so", "libcrypto.so", "libcrypto++.so", "libcryptopp.so", "libsqlite3.so", "libpcap.so"]
lib_dependencies = ["ld-linux-armhf.so.3", "libz.so.1", "libbz2.so.1.0", "libicuuc.so.48", "libicui18n.so.48", "libicudata.so.48"]
lib_names.extend(lib_dependencies)
includes = ["boost", "openssl", "crypto++"] # or "cryptopp", include "sqlite3"

def get_libs(lib_names):
    lib_configs = subprocess.check_output(["ldconfig", "-p"])
    lib_configs = lib_configs.split('\n')
    lib_configs = [ lib_config.split('=>') for lib_config in lib_configs ]
    lib_configs = [ x[1].strip() for x in lib_configs if len(x) == 2 ] #and x[1].endswith(".so") ]
    libs = [ lib_config for lib_name in lib_names for lib_config in lib_configs if lib_name == os.path.basename(lib_config) ]
    return libs

if __name__ == "__main__":
    libs = get_libs(lib_names)
    print libs
    for lib in libs:
        filename = os.path.basename(lib)
        shutil.copy2(lib, os.path.join(os.getcwd(), 'lib', filename))
    # Note: if libcryptopp.so doesn't exist, will need to symlink

# TODO: Copy pkgconfig
# TODO: Copy includes
#for include in includes:
#    print os.path.join('/usr', 'include', include), cwd
#    shutil.copytree(os.path.join('/usr', 'include', include), os.path.join(cwd, include))
