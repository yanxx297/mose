#!/usr/bin/env python

import os
import sys 
import datetime
import clang.cindex
from bs4 import BeautifulSoup

# debug
import pdb

linux_path = "/export/scratch/yanxx297/Project/linux"

files = {}
function_declarations = []  


def traverse(node):
    for child in node.get_children():
        traverse(child)

    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        start = node.extent.start.line
        end = node.extent.end.line
        if not start == end:            
            function_declarations.append(node)


def split_file(filename):
    print(datetime.datetime.now(), "split", filename, "...")
    with open(filename, "r") as f:
        doc = BeautifulSoup(f, "html.parser")
        tags = doc.find_all("div")

        print(datetime.datetime.now(), "Write to split_tree")
        fout = open("split_tree", "w")
        fout.write(str(tags[0]))
        fout.close()
        
        print(datetime.datetime.now(), "Write to right_split")
        fout = open("right_split", "w")
        fout.write(str(tags[1]))
        fout.close()


def get_tests(filename):   
    os.makedirs("code", exist_ok=True)
    os.makedirs("tests", exist_ok=True)

    print(datetime.datetime.now(), "parse", filename, "to collect tests ...")

    with open(filename, "r") as f:
        doc = BeautifulSoup(f, "html.parser")
        tags = doc.find_all("pre")
        print(datetime.datetime.now(), "Initialization complete")

        for tag in tags:
            outfile = tag['id']
            print(datetime.datetime.now(), outfile)
            if outfile.startswith("prog_"):
                outfile = os.path.join("tests", outfile)
            elif outfile.startswith("contents_"):
                outfile = os.path.join("code", outfile)
            else:
                pass
                
            fout = open(outfile, "a")            
#            fout.write(tag.prettify(formatter=None))
            fout.write(str(tag))
            fout.close()


def parse_filelist():
    with open("split_tree", "r") as f, open("filelist.csv", "w") as out:
        doc= BeautifulSoup(f, "html.parser")
        tags = doc.find_all("a")
        for tag in tags:
            if tag["onclick"].split(' ')[0].startswith("onFileClick"):
                id = tag["onclick"].split(' ')[1]
                file = tag["id"].removeprefix("path/")
                files[int(id)] = file
                out.write(file + ";" + id + "\n")


def line_to_func(srcname, linenum):
    filename = srcname.split('/')[-1]

    funcname = ""
    for decl in function_declarations:
        breakpoint()
        start = decl.extent.start.line
        end = decl.extent.end.line  
        if start <= linenum and end >= linenum:
            funcname = decl.displayname
            break

    if funcname == "":
            print("No function found at line %d in %s" % (linenum, filename))
        
    return funcname
        

def parse_code(filename):
    srcname = files[int(filename.split('_')[1])]
    print(datetime.datetime.now(), "Parse", filename, "(", srcname, ")", flush=True)

    # Parse function declarations by clang
    index = clang.cindex.Index.create()
    args = ["-I/export/scratch/yanxx297/Project/linux/include"]
    print(datetime.datetime.now(), "Start traverse()")
    traverse(index.parse(os.path.join(linux_path, srcname), args).cursor)
    print(datetime.datetime.now(), "Finish traverse()")

    print(datetime.datetime.now(), "Start parsing")
    with open(os.path.join("code/",filename), "r") as f, open(os.path.join("coverage/", filename), "w") as out:
        doc = BeautifulSoup(f, "html.parser")
        tags = doc.find_all("td")
        list=tags[0].decode_contents().split('\n')
        for(idx, x) in enumerate(list):
            if not x == '':
                funcname = line_to_func(srcname, idx+1)  
                if not funcname == "":
                    line = BeautifulSoup(x, "html.parser")
                    progname = "prog_"+ line.span["onclick"].split('(')[1].split(',')[0]
                    coverage = (srcname, funcname, progname)
                    out.write("; ".join(coverage) + "\n")
                    #print("%s; %s; %s" % coverage)

    print(datetime.datetime.now(), "Finish parsing")

    # Clean-up function declarations
    function_declarations = []
                


if __name__ == "__main__":
    # Split file to right_split and split_tree
    #split_file("ci-qemu-upstream-0c383648.html")

    # Get code files and tests from right_split
    #get_tests("right_split")   

    # Load file list from split_tree
    parse_filelist()

    # unit test for one code file
    parse_code("contents_2971")
    sys.exit()

    # parse code file to get covered lines
    os.makedirs("coverage", exist_ok=True)
    for filename in os.listdir("code/"):
        parse_code(filename)

