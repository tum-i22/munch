import sys, os
import glob

KLEE_BIN_PATH = "/home/saahil/build/klee/Release+Asserts/bin/"
TESTCASE_I = 0

def read_ktest_to_text(ktest_filename):
    if not os.path.exists(ktest_filename):
        print("ERROR: Path to the ktest file does not exist.")
        return None
    ktest_basename = os.path.basename(ktest_filename)
    os.system("%sktest-tool --write-ints %s > /tmp/%s.txt"%(KLEE_BIN_PATH, ktest_filename, ktest_basename))

    ktest_textfile = open("/tmp/%s.txt"%(ktest_basename), "r")
    return ktest_textfile.readlines()

def parse_meta_block(ktest_text):
    meta_block = []
    for line in ktest_text:
        value = line.split(":")[-1].strip()
        meta_block.append(value)
    return meta_block

def parse_object_block(ktest_text):
    object_block = []

    for line in ktest_text:
        value = line.split(":")[-1].strip().strip("'")
        object_block.append(value)
    return object_block

def parse_ktest(ktest_text):
    meta = []
    objects = []
    
    n_lines = len(ktest_text)
    i = 0

    while (i<n_lines):
        if ktest_text[i].startswith("ktest_file"):
            meta.append(parse_meta_block(ktest_text[i:i+3]))
            i += 2
        elif ktest_text[i].startswith("object"):
            objects.append(parse_object_block(ktest_text[i:i+3]))
            i += 2
        i += 1
    return meta, objects

def get_object_type(o):
    name_line = o[0]

    if name_line.startswith("n_args"):
        return "n_args"
    elif name_line.startswith("arg"):
        return "arg"
    elif name_line.endswith("-data"):
        return "file"
    elif name_line.endswith("-data-stat"):
        return "file-stat"
    elif name_line.startswith("model_version"):
        return "model"

    return "None"

def get_n_args(o):
    name = o[0]
    size = int(o[1])
    data = o[2]
    return name, size, data

def get_full_arg(o):
    name = o[0]
    size = int(o[1])
    data = o[2].split("\\x")[0]
    return name, size, data

def get_full_file(o):
    name = o[0]
    size = int(o[1])
    data = o[2]
    return name, size, data

def get_full_file_stat(o):
    return get_full_arg(o) 

def get_full_model_version(o):
    return get_n_args(o)

def write_files_to_file(testname, objects, out_folder):
    if not os.path.isdir("%s/files"%(out_folder)):
        os.system("mkdir %s/files"%(out_folder))
    for o in objects:
        if o[2]=="":
            continue
        testcase = open("%s/files/%s.%s.txt"%(out_folder, testname, o[0]), "w")
        testcase.write(o[2])
        testcase.close()

def write_args_to_file(testname, objects, out_folder):
    if not os.path.isdir("%s/args"%(out_folder)):
        os.system("mkdir %s/args"%(out_folder))
    testcase = open("%s/args/%s.txt"%(out_folder, testname), "w")
    arg_string = ""
    for o in objects:
        arg_string += o[2] + " "
    if arg_string!="":
        arg_string += "\n"
        testcase.write(arg_string)

def write_testcase_file(testname, objects, out_folder):
    command_args_objects = []
    file_objects = []

    for o in objects:
        type = get_object_type(o)
        if type=="n_args":
            name, size, data = get_n_args(o)
        elif type=="arg":
            name, size, data = get_full_arg(o)
            command_args_objects.append([name, size, data])
        elif type=="file":
            name, size, data = get_full_file(o)
            file_objects.append([name, size, data])
        elif type=="file-stat":
            name, size, data = get_full_file_stat(o)
        elif type=="model":
            name, size, data = get_full_model_version(o)
        else:
            print("Invalid type '%s' read. Ending in panic"%(type))
            sys.exit(-1)

    write_args_to_file(testname, command_args_objects, out_folder)
    write_files_to_file(testname, file_objects, out_folder)

def process_file(ktest_filename):
    # print(ktest_filename)
    ktest_text = read_ktest_to_text(ktest_filename)
    if not ktest_text:
        print("Ending in panic.")
        sys.exit(-1)

    meta, objects = parse_ktest(ktest_text)

    return meta, objects

def process_klee_out(klee_out_name, out_folder):
    global TESTCASE_I
    for t in glob.glob("%s/*.ktest"%(klee_out_name)):
        meta, objects = process_file(t)
        write_testcase_file("test%d"%(TESTCASE_I), objects, out_folder)
        TESTCASE_I += 1

def process_all_klee_outs(parent_dir, out_folder):
    print("Reading all klee-out-* folders in %s"%(parent_dir))
    for f in glob.glob("%s/klee-out-*/"%(parent_dir)):
        print("Reading KLEE testcases from: %s"%(f))
        process_klee_out(f, out_folder)

def main(parent_dir, out_folder):
    process_all_klee_outs(parent_dir, out_folder)

if __name__=="__main__":
    if len(sys.argv)==3:
        klee_out = sys.argv[1]
        out_folder = sys.argv[2]
    elif len(sys.argv)==2:
        klee_out = sys.argv[1]
        if not os.path.isdir("/tmp/testcases"):
            os.system("mkdir /tmp/testcases")
        out_folder = "/tmp/testcases"
    else:
        print("%d arguments given."%(len(sys.argv)))
        print(sys.argv)
        print("Correct usage: read_klee_testcases.py <klee-out-folder> [testcase output folder]")
        sys.exit(-1)

    main(klee_out, out_folder)

