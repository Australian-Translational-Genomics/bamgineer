import sys
import pysam
from uuid import uuid4

inbamfn= sys.argv[1]
outbamfn = sys.argv[2]

inbam = pysam.Samfile(inbamfn, 'rb')
outbam = pysam.Samfile(outbamfn, 'wb', template=inbam)

paired = {}

n = 0
p = 0
u = 0
w = 0
m = 0

for read in inbam.fetch(until_eof=True):
    n += 1
    if read.is_paired:
        p += 1
        if read.qname in paired:
            uuid = paired[read.qname]
            del paired[read.qname]
            read.qname = uuid
            outbam.write(read)
            w += 1
            m += 1
        else:
            newname = str(uuid4())
            paired[read.qname] = newname
            read.qname = newname
            outbam.write(read)
            w += 1
    else:
        u += 1
        read.qname = str(uuid4())
        outbam.write(read)
        w += 1

outbam.close()
inbam.close()