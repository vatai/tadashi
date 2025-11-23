#ifndef SCOP_H
#define SCOP_H

#include <string>

#include <pet.h>

class Scop {
public:
  pet_scop *scop;
  Scop(pet_scop * scop);                ///< Initial constructor.
  virtual ~Scop();                      ///< 1/5 Destructor.
  Scop(const Scop &other);              ///< 2/5 Copy constructor.
  Scop &operator = (const Scop &other); ///< 3/5 Copy assignment.
  Scop(Scop && other);                  ///< 4/5 Move constructor.
  Scop &operator = (Scop && other);     ///< 5/5 Move assignment.
  std::string to_string();
};

#endif
