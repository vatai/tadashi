! =============================================================================
! kernel.f90  --  inner loop kernel
!
! Compiled separately so the profiling driver cannot inline or eliminate
! the kernel calls even at high optimisation levels.
!
! =============================================================================
SUBROUTINE Int2_SumEri( &
 &   ni, nj, nk, nl, nalpbet, mxf, &
 &   twoeri, Fij, Dkl,             &
 &   symmetric_add, compute_exchange, UHF)
!
  IMPLICIT NONE
  INTEGER, INTENT(IN) :: ni, nj, nk, nl, nalpbet, mxf
  REAL(8), INTENT(IN)    :: twoeri(mxf, mxf, mxf, mxf)
  REAL(8), INTENT(INOUT) :: Fij(mxf, mxf, nalpbet)
  REAL(8), INTENT(IN)    :: Dkl(mxf, mxf, nalpbet)
  LOGICAL, INTENT(IN)    :: symmetric_add, compute_exchange, UHF
!
  REAL(8), PARAMETER :: One  = 1.0D+00
  REAL(8), PARAMETER :: Two  = 2.0D+00
  REAL(8), PARAMETER :: Four = 4.0D+00
  INTEGER :: basis_i, basis_j, basis_k, basis_l, ispin
  REAL(8) :: ri_val, den_val, inc_val, scale_factor
!
  IF (compute_exchange) THEN
    IF (ni == nk) THEN
      DO basis_i = 1, ni
        DO basis_j = 1, nj
          DO basis_k = basis_i, nk
            DO basis_l = 1, nl
              ri_val = twoeri(basis_l, basis_k, basis_j, basis_i)
              DO ispin = 1, nalpbet
                den_val = Dkl(basis_j, basis_l, ispin)
                inc_val = den_val*ri_val
                Fij(basis_i, basis_k, ispin) = Fij(basis_i, basis_k, ispin) + inc_val
              END DO
            END DO
          END DO
        END DO
      END DO
    ELSE
      DO basis_i = 1, ni
        DO basis_j = 1, nj
          DO basis_k = 1, nk
            DO basis_l = 1, nl
              ri_val = twoeri(basis_l, basis_k, basis_j, basis_i)
              DO ispin = 1, nalpbet
                den_val = Dkl(basis_j, basis_l, ispin)
                inc_val = den_val*ri_val
                Fij(basis_i, basis_k, ispin) = Fij(basis_i, basis_k, ispin) + inc_val
              END DO
            END DO
          END DO
        END DO
      END DO
    END IF
  ELSE
    IF (.NOT. UHF) THEN
      scale_factor = MERGE(Four, Two, symmetric_add)
      IF (ni == nj) THEN
        DO basis_i = 1, ni
          DO basis_j = basis_i, nj
            DO basis_k = 1, nk
              DO basis_l = 1, nl
                ri_val = twoeri(basis_l, basis_k, basis_j, basis_i)
                den_val = Dkl(basis_k, basis_l, 1)
                inc_val = scale_factor*den_val*ri_val
                Fij(basis_i, basis_j, 1) = Fij(basis_i, basis_j, 1) + inc_val
              END DO
            END DO
          END DO
        END DO
      ELSE
        DO basis_i = 1, ni
          DO basis_j = 1, nj
            DO basis_k = 1, nk
              DO basis_l = 1, nl
                ri_val = twoeri(basis_l, basis_k, basis_j, basis_i)
                den_val = Dkl(basis_k, basis_l, 1)
                inc_val = scale_factor*den_val*ri_val
                Fij(basis_i, basis_j, 1) = Fij(basis_i, basis_j, 1) + inc_val
              END DO
            END DO
          END DO
        END DO
      END IF
    ELSE
      scale_factor = MERGE(Two, One, symmetric_add)
      IF (ni == nj) THEN
        DO basis_i = 1, ni
          DO basis_j = basis_i, nj
            DO basis_k = 1, nk
              DO basis_l = 1, nl
                ri_val = twoeri(basis_l, basis_k, basis_j, basis_i)
                den_val = Dkl(basis_k, basis_l, 1) + Dkl(basis_k, basis_l, 2)
                inc_val = scale_factor*den_val*ri_val
                Fij(basis_i, basis_j, 1:2) = Fij(basis_i, basis_j, 1:2) + inc_val
              END DO
            END DO
          END DO
        END DO
      ELSE
        DO basis_i = 1, ni
          DO basis_j = 1, nj
            DO basis_k = 1, nk
              DO basis_l = 1, nl
                ri_val = twoeri(basis_l, basis_k, basis_j, basis_i)
                den_val = Dkl(basis_k, basis_l, 1) + Dkl(basis_k, basis_l, 2)
                inc_val = scale_factor*den_val*ri_val
                Fij(basis_i, basis_j, 1:2) = Fij(basis_i, basis_j, 1:2) + inc_val
              END DO
            END DO
          END DO
        END DO
      END IF
    END IF
  END IF
!
END SUBROUTINE Int2_SumEri
!

