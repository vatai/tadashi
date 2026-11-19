# Goal

Recreate the code generation capabilities of pluto.

# Specification

If pjsub is on the PATH, you are on the Fugaku supercomputer. You need to submit jobs to the compute nodes. Keep fugaku specific code in launch scripts. Python code should not have any fugaku related code in it. On Fugaku, basically everything has to be executed on compute nodes. You are running on login node, which does not share /tmp with compute nodes.

The paper corresponding to the project is in the paper subfolder. Don't modify the paper unless explicitly asked.

Do not add new source files unless explicitly instructed to. Do not add new functions or make medium or major code changes, only fix things. Don't add checks except where you know for sure that something failed. Always find/show proof of some error happening before implementing unneeded checks to avoid them.

Stop before each git commit. Suggest a commit message and wait for confirmation to proceed.

Pluto fails converting adi.c.

# Plan/Steps

