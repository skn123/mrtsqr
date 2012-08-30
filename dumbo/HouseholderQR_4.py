#!/usr/bin/env dumbo

"""
Householder algorithm driver for MapReduce (part 1)

Austin R. Benson (arbenson@stanford.edu)
David F. Gleich
Copyright (c) 2012
"""

import mrmc
import dumbo
import util
import sys
import os
import HouseholderQR

# create the global options structure
gopts = util.GlobalOptions()

def runner(job):
    mapper = mrmc.ID_MAPPER
    reducer = HouseholderQR.HouseholderRed4()
    job.additer(mapper=mapper, reducer=reducer, opts=[('numreducetasks','1')])

def starter(prog):
    # set the global opts
    gopts.prog = prog

    mat = mrmc.starter_helper(prog, use_full=False, use_house=True)
    if not mat: return "'mat' not specified"

    matname,matext = os.path.splitext(mat)
    output = prog.getopt('output')
    if not output:
        prog.addopt('output','%s-HHQR-4%s'%(matname,matext))

    gopts.save_params()

if __name__ == '__main__':
    dumbo.main(runner, starter)