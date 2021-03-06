#!/usr/bin/env python

class Functions:
    @staticmethod
    def mutateReads(bedfn, bamfn, outfn):
        
        logger.debug("___ mutating reads and finding reads not matching hg19 at germline SNP locations ___")
        samfile = pysam.Samfile(bamfn, "rb" )
        
        outbam = pysam.Samfile(outfn, 'wb', template=samfile) 
        
        
        refbamfn = sub('_het_alt_roi.bam$',"_REFREADS.bam", outfn)
        altbamfn = sub('_het_alt_roi.bam$',"_ALTREADS.bam", outfn)
        
        refbam = pysam.Samfile(refbamfn, 'wb', template=samfile) #SOROUSH
        altbam = pysam.Samfile( altbamfn, 'wb', template=samfile) #SOROUSH
        
        sortedsamfn = sub('.bam$', '.sorted', bamfn)
    
        
        pysam.sort(bamfn, sortedsamfn)
        pysam.index(sortedsamfn+".bam")
        alignmentfile = pysam.AlignmentFile(sortedsamfn+".bam", "rb" )
       
        bedfile = open(bedfn, 'r')
        
        covpath = "/".join([tmpdir, "written_coverage_het.txt"])
        covfile = open(covpath, 'w')
        
        snpratiopath = "/".join([tmpdir, "het_snp_ratio.txt"])
        snpaltratiofile = open(snpratiopath,'w')
        
        writtenreads = []
        readscoveringsnpregion = []
        for bedline in bedfile:
           
            c = bedline.strip().split()
            if (len(c) == 5 ):
                chr2 = c[0]
                chr = c[0].strip("chr")
                start = int(c[1])
                end   = int(c[2])
                refbase = str(c[3])
                altbase = str(c[4])
            else :
                #print(len(c))
                continue
            
            readmappings = alignmentfile.fetch(chr2, start, end)
            readmappingscount = alignmentfile.fetch(chr2, start, end)
            
            total_num_reads_at_this_locus = 0
            num_ref_reads_at_this_locus = 0
            num_non_ref_reads_at_this_locus = 0
            num_reads_written = 0
            for row in readmappingscount:
                total_num_reads_at_this_locus += 2
                
                try:
                    idx = row.get_reference_positions().index(start)
                    nuec = row.seq[idx]
                    if (nuec == refbase):
                        num_ref_reads_at_this_locus += 1
                    else:
                        num_non_ref_reads_at_this_locus += 1
                except (KeyError,ValueError) as e :
                        pass
                if(num_ref_reads_at_this_locus > 0):    
                    ratio = float( num_non_ref_reads_at_this_locus)/float(num_ref_reads_at_this_locus)
                    #print ( "ref/nonref at this locus" + str(ratio ))
                    snpaltratiofile.write(str(ratio )+ '\n')
                else:
                    print("Zero ref reads at this locus")
                    
            
            for shortread in readmappings:
                readscoveringsnpregion.append(shortread.qname)           
                if(shortread.is_paired and shortread.is_proper_pair and not shortread.is_duplicate  
                   and not shortread.is_secondary and not shortread.qname in writtenreads and shortread.mapping_quality >= 30 ):
                    
                    try:
                        index = shortread.get_reference_positions().index(start)
                        nuecleotide = shortread.seq[index]
                        mate = alignmentfile.mate(shortread)
                        
                        if (refbase in bases and nuecleotide in bases ):
                            
                            if(nuecleotide != refbase and nuecleotide == altbase  ):
                                
                                outbam.write(shortread)
                                outbam.write(mate)
                                writtenreads.append(shortread.qname)
                                
                                #altbam.write(shortread)#SOROUSH
                                #altbam.write(mate)
                                num_reads_written += 2
                                continue
                                    
                            elif(nuecleotide == refbase ):
                                
                                refbam.write(shortread)#SOROUSH
                                refbam.write(mate)
                                
                                
                                tmpread = shortread.query_sequence
                                                                        
                                if ((abs(shortread.tlen) > 200)):
                                    #(shortread.is_read2 and index < abs(shortread.tlen) - 100 or  shortread.is_read1 and index > abs(shortread.tlen) - 100 ))):                                  
                                    tmpread = shortread.query_sequence
                                    basetomutate = altbase
                                
                                    for i in range(0, len(tmpread) - 1):              
                                        mutated = tmpread[:index] +  basetomutate + tmpread[index + 1:]
                                    
                                    shortread.query_sequence = mutated
                                    outbam.write(shortread)
                                    outbam.write(mate)
                                    writtenreads.append(shortread.qname)
                                    num_reads_written += 2
                                    #print(str(shortread.is_read1)+'\t'+str(shortread.is_reverse) +'\t'+str(index))
                                    continue       
                                                                             
                    except (KeyError,ValueError) as e :
                        pass  
                #if(num_reads_written >= 1.1*(total_num_reads_at_this_locus / 2.0)): #1.03 changed to 1.1 !
                #if(num_reads_written >= 1.6 * num_non_ref_reads_at_this_locus):    if we adjust the coverage this way it will write in order...last part of the split files wont be written
                    
                #    break
            
            if(float(total_num_reads_at_this_locus) > 0):    
                ratio2 =  float(num_reads_written) / float(total_num_reads_at_this_locus)            
                covfile.write(str(num_reads_written) + '\t' +str(total_num_reads_at_this_locus) + '\t' + 'ratio: '+ str(ratio2) + '\n')
        
        for read in alignmentfile:
            readsaroundsnp = 0 
            if (read.is_proper_pair and read.is_paired and readsaroundsnp < num_non_ref_reads_at_this_locus and
                not read.is_secondary and not read.qname in readscoveringsnpregion and not read.qname in writtenreads):
                
                outbam.write(read)
                readsaroundsnp +=1
                writtenreads.append(read.qname)
                try:
                    outbam.write(alignmentfile.mate(read))
                    writtenreads.append(read.qname)
                                                                                 
                except (KeyError,ValueError) as e :
                    print("no mate found for "+read.qname)
                    pass  
                                   
        outbam.close()
        refbam.close()
        altbam.close()
        covfile.close()
        snpaltratiofile.close()
    
