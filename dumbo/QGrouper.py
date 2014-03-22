"""
Q grouper class used by recursive Direct TSQR.

Use the script run_rec_dirtsqr.py to run recursive Direct TSQR.

Austin R. Benson
David F. Gleich
Copyright (c) 2012-2014
"""

import mrmc
import dumbo
import util
import os
import dirtsqr

# create the global options structure
gopts = util.GlobalOptions()

def runner(job):
    ncols = gopts.getintkey('ncols')
    mapper = dirtsqr.QGrouperMap()
    reducer = dirtsqr.QGrouperReduce(ncols)
    job.additer(mapper=mapper, reducer=reducer,
                opts=[('numreducetasks', str(100))])

def starter(prog):
    # set the global opts
    gopts.prog = prog

    mat = mrmc.starter_helper(prog, True)
    if not mat: return "'mat' not specified"

    gopts.getintkey('ncols', 10)

    matname,matext = os.path.splitext(mat)
    output = prog.getopt('output')
    if not output:
        prog.addopt('output','%s-qgrouped%s'%(matname,matext))

    gopts.save_params()

if __name__ == '__main__':
    dumbo.main(runner, starter)