        program gofr
! ---   Calculation of partial g(r) functions from CPMD output
! ---   Prints out histograms
!
	parameter(nmax=10000)
        parameter(mmmax=8)
        parameter(nhdim=690)
        parameter(nnmax=8)
        parameter(lda=mmmax)
        parameter(lwork=64*nnmax)
	real x(nmax),y(nmax),z(nmax)
	real xo(nmax),yo(nmax),zo(nmax)
	real boxx,boxy,boxz,beta,g(lda,nnmax)
        real gx,gy,gz,apu,bz,dr,rcc
        real gt(nhdim),gg(nhdim),tt(nhdim)
        real sg(nhdim),st(nhdim),ss(nhdim)
        real tg(nhdim),gs(nhdim),ts(nhdim),all(nhdim)  
        real adhoc1,adhoc2,adhoc3,adhoc4,adhoc5,adhoc6
        real adhoc7,adhoc8,adhoc9,adhocc
        double precision a(lda,nnmax),work(lwork)
	integer nions,ipiv(nnmax),ntot,count
        integer gete(nhdim),gege(nhdim),tete(nhdim),kk,ll,mm
        integer tege(nhdim),gesb(nhdim),tesb(nhdim)
        integer sbge(nhdim),sbte(nhdim),sbsb(nhdim),aa(nhdim)
        integer nge,nte,nsb
        character*2 sp(nmax),co         

 	open(10,file='TRAJEC.xyz')
        open(11,file='gofr.hist')

        au=0.529177
        boxx=27.60912  ! Box side, L, in \AA 
        Boxy=27.60912
        boxz=27.60912
        beta=90.0      ! Box angle (cubic)
        pi=acos(-1.0)
        bz=0.02        ! Histogram bin width
        niter=8118     ! Number of iterations
        rcc=13.8       ! Cut-off distance = L/2

        nge=144        ! #Ge
        nte=360        ! #Te
        nsb=144        ! #Sb
        nions=648      ! #atoms

!       V/[(N_A*N_B-N_AB)*dr] --> prefactor in g(r) formula

        adhoc1=boxx*boxy*boxz/(nge*(nge-1))/bz        ! Ge-Ge partial, etc.
        adhoc2=boxx*boxy*boxz/(nge*nsb-(nge+nsb))/bz
        adhoc3=boxx*boxy*boxz/(nge*nte-(nge+nte))/bz
        adhoc4=boxx*boxy*boxz/(nsb*nge-(nsb+nge))/bz
        adhoc5=boxx*boxy*boxz/(nsb*(nsb-1))/bz
        adhoc6=boxx*boxy*boxz/(nsb*nte-(nsb+nte))/bz
        adhoc7=boxx*boxy*boxz/(nte*nge-(nte+nge))/bz
        adhoc8=boxx*boxy*boxz/(nte*nsb-(nte+nsb))/bz
        adhoc9=boxx*boxy*boxz/(nte*(nte-1))/bz
        adhocc=boxx*boxy*boxz/(nions*(nions-1))/bz

        do mm=1,niter         ! Frames
!	
	read(10,*)nions
	read(10,*)co
	do i=1,nions
	read(10,*) sp(i),x(i),y(i),z(i)   ! Read coordinates
        x(i)=x(i)-boxx*nint(x(i)/boxx)    ! Wrap atoms back to the initial supercell
        y(i)=y(i)-boxy*nint(y(i)/boxy)
        z(i)=z(i)-boxz*nint(z(i)/boxz)
        end do	

        beta=beta*pi/180
        if (mod(mm,100).eq.0) then       ! Just printing out tracker
          print*,mm
        end if

        do i=1,nions
         do j=1,nions
         dx=x(i)-x(j)-boxx*nint((x(i)-x(j))/boxx)  ! Calculate distances
         dy=y(i)-y(j)-boxy*nint((y(i)-y(j))/boxy)  ! (only closest replica chosen)
         dz=z(i)-z(j)-boxz*nint((z(i)-z(j))/boxz)
         dr=sqrt(dx*dx+dy*dy+dz*dz)     
!  Ge
          if (dr.le.rcc.and.sp(i).eq.'Ge'.and.sp(j).eq.'Ge'.and.i.ne.j) then
          ll=nint(dr/bz)
          gege(ll)=gege(ll)+1             ! Accumulate histogram for Ge-Ge
          end if
!
          if (dr.le.rcc.and.sp(i).eq.'Ge'.and.sp(j).eq.'Sb') then
          ll=nint(dr/bz)
          gesb(ll)=gesb(ll)+1          
          end if
!
          if (dr.le.rcc.and.sp(i).eq.'Ge'.and.sp(j).eq.'Te') then
          ll=nint(dr/bz)
          gete(ll)=gete(ll)+1
          end if
!  Sb
          if (dr.le.rcc.and.sp(i).eq.'Sb'.and.sp(j).eq.'Ge') then
          ll=nint(dr/bz)
          sbge(ll)=sbge(ll)+1
          end if
!
          if (dr.le.rcc.and.sp(i).eq.'Sb'.and.sp(j).eq.'Sb'.and.i.ne.j) then
          ll=nint(dr/bz)
          sbsb(ll)=sbsb(ll)+1
          end if
!
          if (dr.le.rcc.and.sp(i).eq.'Sb'.and.sp(j).eq.'Te') then
          ll=nint(dr/bz)
          sbte(ll)=sbte(ll)+1
          end if
!  Te
          if (dr.le.rcc.and.sp(i).eq.'Te'.and.sp(j).eq.'Ge') then
          ll=nint(dr/bz)
          tege(ll)=tege(ll)+1
          end if
!
          if (dr.le.rcc.and.sp(i).eq.'Te'.and.sp(j).eq.'Sb') then
          ll=nint(dr/bz)
          tesb(ll)=tesb(ll)+1
          end if
!
          if (dr.le.rcc.and.sp(i).eq.'Te'.and.sp(j).eq.'Te'.and.i.ne.j) then
          ll=nint(dr/bz)
          tete(ll)=tete(ll)+1
          end if
!  ALL
          if (dr.le.rcc.and.i.ne.j) then
          ll=nint(dr/bz)
          aa(ll)=aa(ll)+1
          end if
!
         end do
        end do
!
	end do          !  Frames

        
!-------------------------------------------------------

        do i=1,nhdim
        rbz=bz*i
        gg(i)=adhoc1*gege(i)/(4*pi*rbz*rbz)/niter  ! Final g(r)'s
        gs(i)=adhoc2*gesb(i)/(4*pi*rbz*rbz)/niter  ! divided by 4*\pi*r^2
        gt(i)=adhoc3*gete(i)/(4*pi*rbz*rbz)/niter  ! and number of frames
        sg(i)=adhoc4*sbge(i)/(4*pi*rbz*rbz)/niter
        ss(i)=adhoc5*sbsb(i)/(4*pi*rbz*rbz)/niter
        st(i)=adhoc6*sbte(i)/(4*pi*rbz*rbz)/niter
        tg(i)=adhoc7*tege(i)/(4*pi*rbz*rbz)/niter
        ts(i)=adhoc8*tesb(i)/(4*pi*rbz*rbz)/niter
        tt(i)=adhoc9*tete(i)/(4*pi*rbz*rbz)/niter
        all(i)=adhocc*aa(i)/(4*pi*rbz*rbz)/niter 
!
        write(11,8999)rbz,gg(i),gs(i),gt(i),sg(i),ss(i),st(i),tg(i),ts(i),tt(i),all(i)
        end do

 8989	format(x,(a),6f12.5)
 8999	format(x,f12.5,3x,10f12.5)

	stop
	end

