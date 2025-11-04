// -*- mode:fundamental -*-
%module pytadashi

%include "std_vector.i"
%include "std_string.i"

namespace std {
  %template(StringVector) vector<string>;
};

%{
// extern void free_scops();
#include "ctadashi.h"
%}

// extern void free_scops();
%include "ctadashi.h"