#!/usr/bin/env python3

import os
import stat
import shutil
import io
from subprocess import PIPE, Popen

"""
Copy the hsmtool binary into this directory and them run this script.

Dependent on how hsmtool is build (with TCSAFLUSH or TCSANOW flag in hsm_encryption.c)
this script hangs at count ~100 when simultaneously running `pytest tests/` in another terminal.

The hang can be roduces without runnning `pytest tests/` in parallel, but it takes longer.

Note: manually remove hsm_secret and hsm_secret_orig before running.
"""


hsm_path, hsm_path_orig = 'hsm_secret', 'hsm_secret_orig'
hsmtool_path = os.path.join(os.getcwd(), 'hsmtool') # TCSAFLUSH build, hangs at arround count=100
#hsmtool_path = os.path.join(os.getcwd(), 'hsmtool_TCSANOW') # tested upto count=58k, no problem
language = "0\n"
seed = "ritual idle hat sunny universe pluck key alpha wing cake have wedding\n"
password = "reckless123#{ù}\n"

# generate original hsm_secret, in-one-go
proc_gen = Popen([hsmtool_path, "generatehsm", hsm_path_orig], stdin=PIPE, stdout=PIPE, stderr=PIPE)
proc_gen.communicate(language.encode("utf-8") + seed.encode("utf-8") + password.encode("utf-8"))
assert(proc_gen.wait(timeout=5) == 0)

# use interactive tty to encrypt
mfd, sfd = os.openpty()
mf = io.FileIO(mfd, 'w')

count = 0
while(True):
    # work on a copy of original (unencrypted) hsm_secret
    if os.path.exists('hsm_secret'):
        os.chmod(hsm_path, stat.S_IWUSR)
    shutil.copyfile('hsm_secret_orig', 'hsm_secret')
    os.chmod(hsm_path, stat.S_IRUSR)

    proc = Popen([hsmtool_path, 'encrypt', hsm_path], stdin=sfd, stdout=PIPE, stderr=PIPE)
    resp = proc.stdout.readline()
    assert (resp == b'Enter hsm_secret password:\n')

    mf.write(password.encode('utf-8'))
    resp = proc.stdout.readline()
    assert (resp == b'Confirm hsm_secret password:\n')

    mf.write(password.encode('utf-8'))
    resp = proc.stdout.readline()
    assert (resp == b"Successfully encrypted hsm_secret. You'll now have to pass the --encrypted-hsm startup option.\n")

    assert(proc.wait(timeout=5) == 0)
    count += 1
    print(count)
