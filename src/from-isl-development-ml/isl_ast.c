{
  // 1st level tiling - Tiles
  for (int c0 = 0; c0 <= 32; c0 += 1)
    for (int c1 = 0; c1 <= 32; c1 += 1) {
      // 1st level tiling - Points
      for (int c2 = 0; c2 <= 31; c2 += 1)
        for (int c3 = 0; c3 <= 31; c3 += 1)
          Stmt_12(32 * c0 + c2, 32 * c1 + c3);
    }
  // 1nd level tiling - Tiles
  for (int c0 = 0; c0 <= 65; c0 += 1)
    for (int c1 = 0; c1 <= 3; c1 += 1)
      for (int c2 = 0; c2 <= 10; c2 += 1) {
        // 1nd level tiling - Points
        // Register tiling - Tiles
        for (int c3 = 0; c3 <= 3; c3 += 1)
          for (int c4 = 0; c4 <= 11; c4 += 1)
            for (int c5 = 0; c5 <= 255; c5 += 1) {
              // Register tiling - Points
              for (int c6 = 0; c6 <= 3; c6 += 1)
                for (int c7 = 0; c7 <= 7; c7 += 1)
                  Stmt_17(16 * c0 + 4 * c3 + c6, 96 * c2 + 8 * c4 + c7, 256 * c1 + c5);
            }
      }
}