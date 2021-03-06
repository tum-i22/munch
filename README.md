Munch
======

With two modes (FS and SF), this tool performs a sequence of fuzzing and concolic execution on C programs (compiled into LLVM bitcode). The goal is to increase function coverage and, hopefully, finding more (buffer-overflow) vulnerabilities than symbolic execution or fuzzing. 

[__AFL__](http://lcamtuf.coredump.cx/afl/) is used for (blackbox) fuzzing. Ideally, this stage should cover most of the easy-to-reach functions in the programs. 

[__KLEE22__](https://github.com/tum-i22/klee22/tree/sonar) is used for concolic execution. It is a custom fork of KLEE with a specialized implementation of targeted path search, called *sonar* search. Ideally, this stage should cover the (hard-to-reach) functions that were not discovered with fuzzing in the first step. 

## Prerequisites
Munch requires the following softwares:
- [Macke](https://github.com/tum-i22/macke)
- [AFL](http://lcamtuf.coredump.cx/afl/) 
- KLEE22: This should be installed after Macke's installation
- [afl-cov](https://github.com/mrash/afl-cov)

## Usage

### FS mode
1) Before running FS mode, you should prepare the following files and objects:
- Two different executables, which are generated by compiling the tested program using AFL and KLEE without any optimizations.
- The `afl-cov` results (`afl_output`) from SF mode.
- Configuration file (JSON) 
```
{
    "AFL_OBJECT": "",       # The executable generated by compiling with AFL
    "LLVM_OBJECT": "",      # The bc file generated by compiling with KLEE
    "WHICH_KLEE": "",       # The executable of KLEE
    "AFL_FOLDER_NAME": "",  # The folder name of afl-cov
    "SEARCH_NAME": "",      # The search method to run KLEE
    "TARGET_INFO": "",      # Argument key to the search
    "SYM_STDIN": "",        # Additional arguments (value: stdin) in KLEE
    "SYM_ARGS": "",         # Additional arguments (key) in KLEE
    "SYM_FILES": "",        # Additional arguments (value: file) in KLEE
    "FUNC_TIME": ""         # The value for max-time in KLEE
}
```
2) Basic `--help` output is below:
```
usage: python fs.py [-h] -c CONFIG

Munch FS mode

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the configuration file
```

### SF mode
1) Before running SF mode, you should prepare the following files and objects:
- Three different executables, which are generated by compiling the tested program using AFL, KLEE, and GCOV (with flag `-fprofile-arcs -ftest-coverage`) respectively without any optimizations.
- Configuration file (JSON) 
```
{
    "AFL_BINARY": "",             # The executable generated by compiling with AFL
    "LLVM_OBJ": "",               # The bc file generated by compiling with KLEE
    "GCOV_DIR": "",               # The executable generated by compiling with GCOV
    "LLVM_OPT": "",               # The executable of opt in LLVM
    "LIB_MACKEOPT": "",           # libMackeOpt.so in macke-opt-llvm
    "AFL_BINARY_ARGS": "",        # The arguments for afl-fuzz
    "READ_FROM_FILE": "",
    "AFL_RESULTS_FOLDER": ""。    # The output folder for AFL
}
```
2) Basic `--help` output is below:
```
usage: python sf.py [-h] -c CONFIG -t TIME --klee-out-folder KLEE_OUT_FOLDER
                    --testcase-output-folder TESTCASE_OUTPUT_FOLDER

Munch SF mode

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the configuration file
  -t TIME, --time TIME  The time (second) for fuzzing
  --klee-out-folder KLEE_OUT_FOLDER
                        Path to the folder named klee-out-X
  --testcase-output-folder TESTCASE_OUTPUT_FOLDER
                        Path for storage the testcase for AFL
```

## Misc.

This project is in developmental stage, so please excuse us if it does not work out-of-the-box for you. 

In case of question, simply shoot me an email me at <ognawala@in.tum.de>. 

__N.B.__: You might be interested in our full compositional analysis framework, [__Macke__](https://github.com/tum-i22/macke), for a more vulnerabilities-focussed symbolic execution approach. 
