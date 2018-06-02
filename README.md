# Merge C++ source code back into GCC/G++ assembler output

GCC outputs .file and .loc markers in its assembly output. This program
re-inserts the source code from the referenced locations and unmangles
the C++ identifiers.

The best results are acheived when compiling with `gcc -S -g -fverbose-asm ...`.
