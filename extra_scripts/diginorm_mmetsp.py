import os
import os.path
from os.path import basename
import subprocess
from subprocess import Popen, PIPE
# custom Lisa module
import clusterfunc_py3

def run_streaming_diginorm(trimdir, SRA, diginormdir):
    # from Jessica's streaming protocol:
    diginormfile = diginormdir + SRA + ".stream.diginorm.sh"
    # os.chdir(diginormdir)
    stream_string = """#!/bin/bash
(interleave-reads.py {}{}.trim_1P.fq {}{}.trim_2P.fq && zcat {}orphans.fq.gz)| \\
(trim-low-abund.py -V -k 20 -Z 18 -C 2 - -o - -M 4e9 --diginorm --diginorm-coverage=20) | \\
(extract-paired-reads.py --gzip -p {}{}.paired.gz -s {}{}.single.gz) > /dev/null
""".format(trimdir, SRA, trimdir, SRA, trimdir, diginormdir, SRA, diginormdir, SRA)
    print(stream_string)
    # with open(diginormfile,"w") as diginorm_script:
    #   diginorm_script.write(stream_string)
    #s=subprocess.Popen("sudo bash "+diginormfile,shell=True)
    # s.wait()
    # print "file written:",diginormfile
    # os.chdir("/home/ubuntu/MMETSP/")
    streaming_diginorm_command = [stream_string]
    module_load_list = []
    process_name = "diginorm_stream"
    clusterfunc_py3.qsub_file(diginormdir, process_name,
                          module_load_list, SRA, streaming_diginorm_command)


def interleave_reads(mmetsp_dir, mmetsp):
    interleave_string = """
cd {}
for filename in *.trim_1P.fq
do
	base=$(basename $filename .fq)
	echo $base
	base2=${{base/_1P/_2P}}
	echo $base2
	output=${{base/_1P/}}.interleaved.fq
	#echo $output
	(interleave-reads.py ${{base}}.fq ${{base2}}.fq | gzip > $output)
done
""".format(mmetsp_dir)
    print(interleave_string)
    interleave_command = [interleave_string]
    process_name = "interleave"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = mmetsp
    clusterfunc_py3.qsub_file(mmetsp_dir, process_name,
                              module_name_list, filename, interleave_command)


def run_diginorm(diginormdir, interleavedir, trimdir, sra):
    normalize_median_string = """
normalize-by-median.py -p -k 20 -C 20 -M 4e9 \\
--savegraph {}norm.C20k20.ct \\
-u {}orphans.fq.gz \\
{}*.fq
""".format(diginormdir, trimdir, interleavedir)
    normalize_median_command = [normalize_median_string]
    process_name = "diginorm"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = sra
    clusterfunc_py3.qsub_file(diginormdir, process_name,
                          module_name_list, filename, normalize_median_command)


def run_filter_abund(diginormdir, sra):
    keep_dir = diginormdir + "qsub_files/"
    filter_string = """
filter-abund.py -V -Z 18 {}norm.C20k20.ct {}*.keep
""".format(diginormdir, keep_dir)
    extract_paired_string = extract_paired(diginormdir)
    commands = [filter_string, extract_paired_string]
    process_name = "filtabund"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = sra
    clusterfunc_py3.qsub_file(diginormdir, process_name,
                          module_name_list, filename, commands)

def extract_paired(mmetsp_dir):
    extract_paired_string = """
cd {}qsub_files/
for file in *.abundfilt
do
	extract-paired-reads.py ${{file}}
done
""".format(mmetsp_dir)
    return extract_paired_string

def run_diginorm(mmetsp_dir,mmetsp):
    normalize_median_string = """
normalize-by-median.py -p -k 20 -C 20 -M 4e9 \\
--savegraph {}norm.C20k20.ct \\
-u {}orphans.fq.gz \\
{}*.interleaved.fq
""".format(mmetsp_dir,mmetsp_dir,mmetsp_dir)
    #s=subprocess.Popen("cat diginorm.sh",shell=True)
    # s.wait()
    normalize_median_command = [normalize_median_string]
    process_name = "diginorm"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = mmetsp
    clusterfunc_py3.qsub_file(mmetsp_dir, process_name,
                          module_name_list, filename, normalize_median_command)

def combine_orphaned(mmetsp_dir,item):
    j = """
cd {}qsub_files
rm -rf orphans.keep.abundfilt.fq.gz
gzip -9c orphans.fq.gz.keep.abundfilt > orphans.keep.abundfilt.fq.gz
for file in *.se
do
	gzip -9c ${{file}} >> orphans.keep.abundfilt.fq.gz
done
""".format(mmetsp_dir)
    return j

def rename_pe(mmetsp_dir,item):
    j = """
for file in *trim.interleaved.fq.keep.abundfilt.pe
do
	newfile=${{file%%.fq.keep.abundfilt.pe}}.keep.abundfilt.fq
	cp ${{file}} ${{newfile}}
	gzip ${{newfile}}
done
""".format()
    return j

def split_reads(mmetsp_dir,item):
    split_command="""
for file in *.trim.interleaved.keep.abundfilt.fq.gz
do
   split-paired-reads.py ${{file}}
done
""".format(mmetsp_dir)
    return split_command

def combine(mmetsp_dir,item):
    j="""
cat *.1 > {}{}.left.fq
cat *.2 > {}{}.right.fq
gunzip -c *orphans.keep.abundfilt.fq.gz >> {}{}.left.fq
""".format(mmetsp_dir,item,mmetsp_dir,item,mmetsp_dir,item)
    return j

def consolidate(mmetsp_dir,item):
    combine_orphaned_string = combine_orphaned(mmetsp_dir,item)
    rename_pe_string = rename_pe(mmetsp_dir,item)
    split_reads_string = split_reads(mmetsp_dir,item)
    combine_string = combine(mmetsp_dir,item)
    consolidate_commands=[combine_orphaned_string,rename_pe_string,split_reads_string,combine_string]
    process_name="consolidate"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    clusterfunc_py3.qsub_file(mmetsp_dir,process_name,module_name_list,item,consolidate_commands)

def execute(basedir, listofdirs):
    for item in listofdirs:
        print(item)
        mmetsp_dir = basedir+item+"/"
    	interleave_reads(mmetsp_dir,item)
        run_diginorm(mmetsp_dir,item)
        run_filter_abund(mmetsp_dir, item)
        #consolidate(mmetsp_dir,item)

basedir = "/mnt/home/ljcohen/special_flowers/"
listofdirs = os.listdir(basedir)
execute(basedir, listofdirs)
