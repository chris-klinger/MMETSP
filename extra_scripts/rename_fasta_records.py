import screed
import os
from os import path


def execute(basedir,assemblies,renamed):
     for fasta_filename in assemblies:
         fasta_file = basedir + fasta_filename
         new_filename = renamed + fasta_filename+ ".renamed.fasta"
         mmetsp = fasta_filename.split(".")[0]
         print(mmetsp)
         with open(new_filename,'w') as fp:
             for n, record in enumerate(screed.open(fasta_file)):
                 name = """{}_NCGR_{}""".format(mmetsp,record.name)
                 fp.write(">{name}\n{seq}\n".format(name=name, seq=record.sequence))  

basedir = "/mnt/research/ged/lisa/dammit_annotations/imicrobe_fasta/"
renamed = "/mnt/research/ged/lisa/dammit_annotations/imicrobe_fasta_renamed/"
assemblies = os.listdir(basedir)
execute(basedir,assemblies,renamed)
print("Files written:",renamed)