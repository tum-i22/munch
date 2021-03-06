import os, sys
import subprocess, time, signal
import json
# from collections import OrderedDict
import essentials as es
from helper import read_config

global AFL_OBJ, WHICH_KLEE, LLVM_OBJ, TESTCASES, FUZZ_TIME, GCOV_DIR, LLVM_OPT, LIB_MACKEOPT, AFL_BINARY_ARGS, READ_FROM_FILE, OUTPUT_DIR, AFL_RESULTS_FOLDER, KLEE_RESULTS_FOLDER, FUZZ_TIME

def run_afl_cov(prog, prog_args, read_from_file, path_to_afl_results, gcov_obj, code_dir):
    afl_out_res = path_to_afl_results
    write_func = afl_out_res + "/covered_functions.txt"
    
    func_list = []

    if os.path.isfile(write_func):
        func_file = open(write_func)
        for line in func_file:
            func_list.append(line.strip())
        return func_list
    
    if "@@" in read_from_file:
        #file_redirect, extra_args = read_from_file.split()[0].replace("@@", "<<"), " ".join(read_from_file.split()[1:])
        file_redirect, extra_args = "", " ".join(read_from_file.split()[1:])
    else:
        file_redirect, extra_args = "<<", ""
    
    command = '"' + gcov_obj + ' ' + prog_args + ' ' + file_redirect + ' AFL_FILE ' + extra_args + '"'
    print(command)
    #pos = code_dir.rfind('/')
    #code_dir = code_dir[:pos + 1]
    args = ['afl-cov', '-d', afl_out_res, '-e', command, '-c', code_dir, '--coverage-include-lines', '-O']
    #print(args)
    #subprocess.call(args)
    os.system(" ".join(args))#+" >/dev/null 2>&1")

    # get function coverage
    cov_dir = afl_out_res + "/cov/"
    filename = cov_dir + "id-delta-cov"
    f_cov = open(filename, "r")
    next(f_cov)

    f = open(write_func, "w+")

    for line in f_cov:
        words = line.split(" ")
        if "function" in words[3]:
            func_list.append(words[4][:-3])
            f.write(words[4][:-3] + "\n")

    f.close()
    f_cov.close()

    return func_list


def order_funcs_topologic(list_of_functions):
    func = ""
    l = []
    for c in list_of_functions:
        if c not in "[],\n\"":
            if (c == ' ') and (func != ""):
                l.append(func)
                func = ""
            else:
                if c != ' ':
                    func += c
    if func != "":
        l.append(func)

    l.reverse()
    #print(l)
    return l


def main(config_file, klee_time, afl_time, output):
    read_config(config_file, klee_time, afl_time, output)

    testcase = es.TESTCASES

    if not os.path.isdir(testcase):
        print("Testcases directory does not exist: %s"%(testcase))
        print("Exiting...")
        return -1

    fuzz_time = 0
    try:
        fuzz_time = int(es.FUZZ_TIME)
    except ValueError:
        print("Fuzz time invalid: %s"%(es.FUZZ_TIME))
        return -1
    
    # get a list of functions topologically ordered
    args = [es.LLVM_OPT, "-load", es.LIB_MACKEOPT, es.LLVM_OBJ,
            "--listallfuncstopologic", "-disable-output"]
    result = subprocess.check_output(args)
    #result = [r.strip("\\n") for r in result]
    result = str(result, 'utf-8')

    '''
    print("TOTAL FUNCS : ")
    print(len(all_funcs_topologic))
    time.sleep(3)
    '''

    all_funcs_topologic = order_funcs_topologic(result)
    # run afl-fuzz
    #pos = es.AFL_BINARY.rfind('/')
    if not os.path.isdir(es.AFL_RESULTS_FOLDER):
        args = ["afl-fuzz", "-i", testcase, "-o", es.AFL_RESULTS_FOLDER, es.AFL_OBJ, es.AFL_BINARY_ARGS, es.READ_FROM_FILE]
        # take the progs args as given from command line
        # if sys.argv[5:]:
        #    args = args + sys.argv[5:]

        print("Preparing to fuzz...")
        time.sleep(2)
        proc = subprocess.Popen(args)

        time.sleep(int(fuzz_time))
        print("Killing AFL")
        os.kill(proc.pid, signal.SIGINT)
    else:
        print("That directory already contains past fuzzing results.")
        print("Continuing with coverage calculation...")
        time.sleep(1)
    
    # run KLEE with targeted search with the functions not covered by afl
    # be sure it's topologically sorted
    print("Computing function coverage after fuzzing...")
    time.sleep(2)
    func_list_afl = run_afl_cov(es.AFL_OBJ, es.AFL_BINARY_ARGS, es.READ_FROM_FILE, es.AFL_RESULTS_FOLDER, es.GCOV_OBJ, es.GCOV_DIR)
    #print("AFL LIST: ")
    print("%d functions covered by AFL."%len(func_list_afl))
    #print(func_list_afl)

    uncovered_funcs = []
    for index in range(len(all_funcs_topologic)):
        if all_funcs_topologic[index] not in func_list_afl:
            uncovered_funcs.append(all_funcs_topologic[index])

    #print("UNCOVERED LIST: ")
    print("%d functions to be targeted by symbolic execution."%len(uncovered_funcs))
    #print(uncovered_funcs)

    # save the list of covered and uncovered functions after fuzzing
    """
    cov_funcs = AFL_OUT + "/covered_functions.txt"
    with open(cov_funcs, 'w+') as the_file:
        the_file.write("%s\n" %len(func_list_afl))
        for index in range(len(func_list_afl)):
            the_file.write("%s\n" %func_list_afl[index])
    """
    uncov_funcs = es.AFL_RESULTS_FOLDER + "/uncovered_functions.txt"
    with open(uncov_funcs, 'w+') as the_file:
        the_file.write("%s\n" % len(uncovered_funcs))
        for index in range(len(uncovered_funcs)):
            the_file.write("%s\n" % uncovered_funcs[index])

    return 1

if __name__ == '__main__':
    try:
        config_file = sys.argv[1]
        testcase = sys.argv[2]  # testcases for the program used by afl-fuzz
        fuzz_time = int(sys.argv[3])  # time to run afl-fuzzer
    except IndexError:
        print("Wrong number of command line args:", sys.exc_info()[0])
        raise

    main(config_file, testcase, fuzz_time)
