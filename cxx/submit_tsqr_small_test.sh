#!/bin/bash
#   Copyright (c) 2012-2014, Austin Benson and David Gleich
#   All rights reserved.
#
#   This file is part of MRTSQR and is under the BSD 2-Clause License, 
#   which can be found in the LICENSE file in the root directory, or at 
#   http://opensource.org/licenses/BSD-2-Clause

HADOOP_DIR=/home/mrhadoop/hadoop-0.21.0
STREAMING_JAR=$HADOOP_DIR/mapred/contrib/streaming/hadoop-0.21.0-streaming.jar

hadoop fs -rmr matfiles/small-test-qrr.mseq

hadoop jar $STREAMING_JAR -input matfiles/small-test.mseq -output matfiles/small-test-qrr.mseq \
  -jobconf mapreduce.job.name=tsqr_cxx \
  -jobconf 'stream.map.input=typedbytes' -jobconf 'stream.reduce.input=typedbytes' \
  -jobconf 'stream.map.output=typedbytes' -jobconf 'stream.reduce.output=typedbytes' \
  -outputformat 'org.apache.hadoop.mapred.SequenceFileOutputFormat' \
  -inputformat 'org.apache.hadoop.streaming.AutoInputFormat' \
  -file tsqr -mapper './tsqr map' -reducer './tsqr reduce' \

hadoop jar $STREAMING_JAR dumptb matfiles/small-test-qrr.mseq | ./dump_typedbytes_info -  
