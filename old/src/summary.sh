#!/bin/bash

# Generate a summary of all the source files.

ls $(dirname $0)/*.c* | while read ccfile; do
    header=$(basename ${ccfile})
    echo ${header}
    echo $(echo ${header} | sed -e 's/./=/g')
    cat ${ccfile} | sed -e '/Emil Vatai/b quit;/Copyright/b quit;/#include/b quit;s/.\*[^a-zA-Z]*//;b end;: quit s/.*//;q;: end;'
done | less
