program main
  implicit none
  integer, parameter :: N = 1000
  real(8) :: A(N, N)
  integer :: i, count_rate, count_start, count_end
  real(8) :: walltime

  call random_seed()

  do i = 1, N
     call init_arr(N, A(i, :))
  end do

  call system_clock(count_start, count_rate)

  do i = 1, 10
     call f(N, A)
  end do

  call system_clock(count_end)

  walltime = real(count_end - count_start, 8) * 1000.0d0 / real(count_rate, 8)
  print *, "WALLTIME:", int(walltime)

contains

  subroutine print_arr(N, A)
    integer, intent(in) :: N
    real(8), intent(in) :: A(N)
    integer :: i
    do i = 1, N
       write(*,'(F10.6, A)', advance='no') A(i), ", "
    end do
    print *
  end subroutine print_arr

  subroutine init_arr(N, A)
    integer, intent(in) :: N
    real(8), intent(out) :: A(N)
    integer :: i
    do i = 1, N
       call random_number(A(i))
    end do
  end subroutine init_arr

  subroutine f(N, A)
    integer, intent(in) :: N
    real(8), intent(inout) :: A(N, N)
    integer :: i, j
    do j = 2, N
       do i = 2, N
          A(i, j) = (A(i, j - 1) + A(i, j)) / 2.0d0
       end do
    end do
  end subroutine f

end program main
