"""
   Copyright (c) 2012-2014, Austin Benson and David Gleich
   All rights reserved.

   This file is part of MRTSQR and is under the BSD 2-Clause License, 
   which can be found in the LICENSE file in the root directory, or at 
   http://opensource.org/licenses/BSD-2-Clause
"""

"""
This is a script to run the Direct TSQR algorithm with direct computation
of the matrix Q.  This script can also be used for direct computation
of the left singular vectors (along with the singular values and right
singular vectors).

See options:
     python run_direct_tsqr.py --help

Example usage:
     python run_direct_tsqr.py --input=A_800M_10.bseq \
            --ncols=10 --svd=2 --schedule=100,100,100 \
            --hadoop=icme-hadoop1 --local_output=tsqr-tmp \
            --output=DIRTSQR_TESTING
"""

import os
import shutil
import subprocess
import sys
import time
import util
from optparse import OptionParser

# Parse command-line options
#
# TODO(arbenson): use argparse instead of optparse when icme-hadoop1 defaults
# to python 2.7
parser = OptionParser()
parser.add_option('-i', '--input', dest='input', default='',
                  help='input matrix')
parser.add_option('-o', '--output', dest='out', default='',
                  help='base string for output of Hadoop jobs')
parser.add_option('-l', '--local_output', dest='local_out', default='direct_out_tmp',
                  help='Base directory for placing local files')
parser.add_option('-t', '--times_output', dest='times_out', default='times',
                  help='file for storing command times')
parser.add_option('-n', '--ncols', type='int', dest='ncols', default=0,
                  help='number of columns in the matrix')
parser.add_option('-s', '--schedule', dest='sched', default='100,100,100',
                  help='comma separated list of number of map tasks to use for'
                       + ' the three jobs')
parser.add_option('-H', '--hadoop', dest='hadoop', default='',
                  help='name of hadoop for Dumbo')
parser.add_option('-x', '--svd', type='int', dest='svd', default=0,
                  help="""0: no SVD computed;
1: compute the singular values (R = USV^t);
2: compute the singular vectors as well as QR;
3: compute the SVD but not the QR factorization
"""
)
parser.add_option('-q', '--quiet', action='store_false', dest='verbose',
                  default=True, help='turn off some statement printing')

(options, args) = parser.parse_args()
cm = util.CommandManager(verbose=options.verbose)

# Store options in the appropriate variables
in1 = options.input
if in1 == '':
  cm.error('no input matrix provided, use --input')

out = options.out
if out == '':
  # TODO(arbenson): make sure in1 is clean
  out = in1 + '_DIRECT'

local_out = options.local_out
out_file = lambda f: local_out + '/' + f
if os.path.exists(local_out):
  shutil.rmtree(local_out)
os.mkdir(local_out)

times_out = options.times_out

ncols = options.ncols
if ncols == 0:
  cm.error('number of columns not provided, use --ncols')

svd_opt = options.svd

sched = options.sched
try:
  sched = [int(s) for s in sched.split(',')]
  sched[2]
except:
  cm.error('invalid schedule provided')

hadoop = options.hadoop

run_recursive = True

# Now run the MapReduce jobs
out1 = out + '_1'
cm.run_dumbo('dirtsqr1.py', hadoop, ['-mat ' + in1, '-output ' + out1,
                                     '-nummaptasks %d' % sched[0],
                                     '-libjar feathers.jar'])

out2 = out + '_2'
cm.run_dumbo('dirtsqr2.py', hadoop, ['-mat ' + out1 + '/R_*', '-output ' + out2,
                                     '-svd ' + str(svd_opt),
                                     '-nummaptasks %d' % sched[1],
                                     '-libjar feathers.jar'])

# Q2 file needs parsing before being distributed to phase 3
Q2_file = out_file('Q2.txt')

if os.path.exists(Q2_file):
  os.remove(Q2_file)

if os.path.exists(Q2_file + '.out'):
  os.remove(Q2_file + '.out')

cm.copy_from_hdfs(out2 + '/Q2', Q2_file)
cm.parse_seq_file(Q2_file)

if svd_opt in [2, 3]:
  small_U_file = out_file('U.txt')

  if os.path.exists(small_U_file):
    os.remove(small_U_file)
  if os.path.exists(small_U_file + '.out'):
    os.remove(small_U_file + '.out')

  cm.copy_from_hdfs(out2 + '/U', small_U_file)
  cm.parse_seq_file(small_U_file)

in3 = out1 + '/Q_*'
opts = ['-mat ' + in3, '-output ' + out + '_3', '-ncols ' + str(ncols),
        '-q2path ' + Q2_file + '.out', '-nummaptasks %d' % sched[2],
        '-libjar feathers.jar']
if svd_opt == 3:
  opts += ['-upath ' + small_U_file + '.out']
cm.run_dumbo('dirtsqr3.py', hadoop, opts)

if svd_opt == 2:
  # We need an addition TS matrix multiply to get the left singular vectors
  out4 = out + '_4'

  cm.run_dumbo('TSMatMul.py', hadoop, ['-mat ' + out + '_3', '-output ' + out4,
                                       '-mpath ' + small_U_file + '.out',
                                       '-nummaptasks %d' % sched[2]])

try:
  f = open(times_out, 'a')
  f.write('times: ' + str(cm.times) + '\n')
  f.close
except:
  print str(cm.times)
