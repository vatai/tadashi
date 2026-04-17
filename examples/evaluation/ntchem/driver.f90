! =============================================================================
! driver.f90  --  profiling kernel.f90
!
! Enumerates all (ni, nj, nk, nl) shell quartets up to H angular momentum
! for both spherical and Cartesian basis functions, times BATCH calls of
! the kernel for each case, and reports the per-call average.
!
! Shell sizes:
!   Spherical:  s=1  p=3  d=5  f=7  g=9  h=11    (2L+1)
!   Cartesian:  s=1  p=3  d=6  f=10 g=15 h=21    ((L+1)(L+2)/2)
!
! Usage:
!   ./driver [options]
!
! Options:
!   --uhf            UHF=.TRUE.,  nalpbet=2
!   --rhf            UHF=.FALSE., nalpbet=1  (default)
!   --exchange       compute_exchange=.TRUE.  (default)
!   --coulomb        compute_exchange=.FALSE.
!   --symmetric      symmetric_add=.TRUE.
!   --nosymmetric    symmetric_add=.FALSE.    (default)
! =============================================================================
PROGRAM driver
  IMPLICIT NONE
!
  ! ---- Angular momentum up to G --------------------------------------------
  INTEGER, PARAMETER :: MAXL = 5
!
  ! Shell sizes: index 0..MAXL
  INTEGER, PARAMETER :: SPH_SIZES(0:MAXL) = (/ 1, 3, 5, 7, 9, 11 /)    ! 2L+1
  INTEGER, PARAMETER :: CAR_SIZES(0:MAXL) = (/ 1, 3, 6, 10, 15, 21 /)  ! (L+1)(L+2)/2
!
  INTEGER, PARAMETER :: MXF_SPH = 11   ! max spherical functions per shell
  INTEGER, PARAMETER :: MXF_CAR = 21   ! max Cartesian functions per shell
!
  ! ---- runtime options (defaults) ------------------------------------------
  LOGICAL :: UHF           = .FALSE.
  LOGICAL :: compute_exchange = .TRUE.
  LOGICAL :: symmetric_add = .FALSE.
!
  ! ---- arrays (sized for Cartesian H: 21^4 * 8 bytes ~ 32 MB) -------------
  REAL(8) :: twoeri(MXF_CAR, MXF_CAR, MXF_CAR, MXF_CAR)
  REAL(8) :: Fij_base(MXF_CAR, MXF_CAR, 2)
  REAL(8) :: Fij(MXF_CAR, MXF_CAR, 2)
  REAL(8) :: Dkl(MXF_CAR, MXF_CAR, 2)
!
  ! ---- locals --------------------------------------------------------------
  INTEGER :: nalpbet, mxf
  INTEGER :: li, lj, lk, ll, ni, nj, nk, nl
  INTEGER :: ibatch, ibasis
  INTEGER, PARAMETER :: BATCH = 1000 ! calls per timed measurement
  INTEGER(8) :: t_start, t_end, count_rate
  REAL(8) :: best_us, checksum
  CHARACTER(len=64) :: arg
  INTEGER :: iarg, nargs
!
! =============================================================================
! 1. Parse command line
! =============================================================================
  nargs = COMMAND_ARGUMENT_COUNT()
  iarg  = 1
  DO WHILE (iarg <= nargs)
    CALL GET_COMMAND_ARGUMENT(iarg, arg)
    SELECT CASE (TRIM(arg))
      CASE ('--uhf');         UHF             = .TRUE.
      CASE ('--rhf');         UHF             = .FALSE.
      CASE ('--exchange');    compute_exchange = .TRUE.
      CASE ('--coulomb');     compute_exchange = .FALSE.
      CASE ('--symmetric');   symmetric_add   = .TRUE.
      CASE ('--nosymmetric'); symmetric_add   = .FALSE.
      CASE DEFAULT
        WRITE(*,'("unknown option: ",A)') TRIM(arg);  STOP 1
    END SELECT
    iarg = iarg + 1
  END DO
!
  nalpbet = MERGE(2, 1, UHF)
!
! =============================================================================
! 2. Fill arrays with random data once -- reused for all cases
! =============================================================================
  CALL RANDOM_NUMBER(twoeri);  twoeri   = 2.0D0*twoeri   - 1.0D0
  CALL RANDOM_NUMBER(Fij_base); Fij_base = 2.0D0*Fij_base - 1.0D0
  CALL RANDOM_NUMBER(Dkl);     Dkl      = 2.0D0*Dkl      - 1.0D0
  CALL SYSTEM_CLOCK(COUNT_RATE=count_rate)
  checksum = 0.0D0
!
! =============================================================================
! 3. Header
! =============================================================================
  WRITE(*,'(A)') '# Int2_SumEri profile'
  WRITE(*,'(A,I0,A)') '# batch=', BATCH, &
 &  MERGE('  exchange', '  coulomb ', compute_exchange) // &
 &  MERGE('  UHF', '  RHF', UHF) // &
 &  MERGE('  symmetric  ', '  nosymmetric', symmetric_add)
  WRITE(*,'(A)') '#'
  WRITE(*,'(A)') '# basis     ni  nj  nk  nl   total_us(batch)'
  WRITE(*,'(A)') '# ------   --  --  --  --   ---------------'
!
! =============================================================================
! 4. Enumerate -- spherical then Cartesian
! =============================================================================
  DO ibasis = 1, 2
    IF (ibasis == 1) THEN
      mxf = MXF_SPH
    ELSE
      mxf = MXF_CAR
    END IF
!
    DO li = 0, MAXL
    DO lj = 0, MAXL
    DO lk = 0, MAXL
    DO ll = 0, MAXL
      IF (ibasis == 1) THEN
        ni = SPH_SIZES(li);  nj = SPH_SIZES(lj)
        nk = SPH_SIZES(lk);  nl = SPH_SIZES(ll)
      ELSE
        ni = CAR_SIZES(li);  nj = CAR_SIZES(lj)
        nk = CAR_SIZES(lk);  nl = CAR_SIZES(ll)
      END IF
!
      ! Time BATCH calls in one shot and divide.
      Fij = Fij_base
      CALL SYSTEM_CLOCK(t_start)
      DO ibatch = 1, BATCH
        CALL Int2_SumEri( &
       &   ni, nj, nk, nl, nalpbet, mxf, &
       &   twoeri, Fij, Dkl,             &
       &   symmetric_add, compute_exchange, UHF)
      END DO
      CALL SYSTEM_CLOCK(t_end)
      checksum = checksum + SUM(Fij)   ! defeat dead-code elimination
      best_us = REAL(t_end - t_start, 8) / REAL(count_rate, 8) * 1.0D6
!
      WRITE(*,'(A8,2X,4I4,3X,ES14.6)') &
     &  MERGE('sph     ', 'cart    ', ibasis==1), &
     &  ni, nj, nk, nl, best_us
!
    END DO
    END DO
    END DO
    END DO
!
    WRITE(*,*)   ! blank line between spherical and Cartesian blocks
  END DO
!
  WRITE(*,'("# checksum ",ES14.6)') checksum  ! confirms kernel ran
  STOP 0
!
! =============================================================================
!
END PROGRAM driver

