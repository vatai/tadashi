// -*- mode:fundamental -*-
%module pytadashi

%include "std_vector.i"
%include "std_string.i"

namespace std {
  %template(StringVector) vector<string>;
};

%{
#include "ctadashi.h"
%}

%include "ctadashi.h"