%define         major 4
%define         liblrs %mklibname lrs %{major}
%define         liblrs_devel %mklibname -d lrs

Name:           lrslib
Group:          Sciences/Mathematics
Version:        4.3
Release:        4%{?dist}
Summary:        Reverse search for vertex enumeration/convex hull problems

%global upver 0%(echo %{version} | sed 's/\\.//')

License:        GPLv2+
URL:            http://cgm.cs.mcgill.ca/~avis/C/lrs.html
Source0:        http://cgm.cs.mcgill.ca/~avis/C/%{name}/%{name}-%{upver}.tar.gz
# These man pages were written by Jerry James.  Text from the sources was used,
# therefore the man pages have the same copyright and license as the sources.
Source1:        %{name}-man.tar.xz
# This patch was sent upstream on 31 May 2011.  It fixes some miscellaneous
# bugs and adapts to the naming scheme we choose for installation.
Patch0:         %{name}-fixes.patch
# This patch is from Thomas Rehn, who also sent the patch upstream.  It fixes
# a memory leak.
Patch1:         %{name}-memleak.patch

BuildRequires:  gmp-devel

%description
%{name} is a self-contained ANSI C implementation as a callable library
of the reverse search algorithm for vertex enumeration/convex hull
problems and comes with a choice of three arithmetic packages.  Input
file formats are compatible with Komei Fukuda's cdd package (cddlib).
All computations are done exactly in either multiple precision or fixed
integer arithmetic.  Output is not stored in memory, so even problems
with very large output sizes can sometimes be solved.

%package -n %{liblrs}
Summary:        Reverse search for vertex enumeration/convex hull problems

%description -n %{liblrs}
%{name} is a self-contained ANSI C implementation as a callable library
of the reverse search algorithm for vertex enumeration/convex hull
problems and comes with a choice of three arithmetic packages.  Input
file formats are compatible with Komei Fukuda's cdd package (cddlib).
All computations are done exactly in either multiple precision or fixed
integer arithmetic.  Output is not stored in memory, so even problems
with very large output sizes can sometimes be solved.

%package -n %{liblrs_devel}
Summary:        Header files and libraries for developing with %{name}
Requires:       %{liblrs}%{?_isa} = %{version}-%{release}
Provides:       %{name}-devel = %{version}-%{release}
Requires:       gmp-devel%{?_isa}

%description -n %{liblrs_devel}
Header files and libraries for developing with %{name}.

%prep
%setup -q -n %{name}-%{upver}
%setup -q -n %{name}-%{upver} -T -D -a 1
%patch0

# Fix the FSF's address
for f in COPYING lrsgmp.h lrslib.{c,h} lrslong.h lrsmp.{c,h}; do
  sed -i.orig \
    's/675 Mass Ave, Cambridge, MA 02139/51 Franklin Street, Suite 500, Boston, MA  02110-1335/' \
    $f
  touch -r $f.orig $f
  rm -f $f.orig
done

%build
# The Makefile is too primitive to use.  For one thing, it only builds
# binaries, not libraries.  We do our own thing here.

# Extract the version numbers to be used for the shared libraries.
%global ver %(echo %{version} | sed -r 's/([\\\.[:digit:]]*)[[:alpha:]]/\\\1/')
%global sover %(echo %{version} | cut -d. -f1)

CFLAGS="${RPM_OPT_FLAGS} -DTIMES -DSIGNALS"
if [ %{__isa_bits} = "64" ]; then
  CFLAGS+=" -DB64"
fi

# Build the GMP version of the library
gcc $CFLAGS -DGMP -fPIC -shared -o liblrsgmp.so.%{ver} \
    -Wl,-soname,liblrsgmp.so.%{sover} lrslib.c lrsgmp.c -lgmp
ln -s liblrsgmp.so.%{ver} liblrsgmp.so.%{sover}
ln -s liblrsgmp.so.%{sover} liblrsgmp.so

# Build the integer version of the library
gcc $CFLAGS -DLONG -fPIC -shared -o liblrslong.so.%{ver} \
    -Wl,-soname,liblrslong.so.%{sover} lrslib.c lrslong.c
ln -s liblrslong.so.%{ver} liblrslong.so.%{sover}
ln -s liblrslong.so.%{sover} liblrslong.so

# Build the multi-precision version of the library
gcc $CFLAGS -DLRSMP -fPIC -shared -o liblrsmp.so.%{ver} \
    -Wl,-soname,liblrsmp.so.%{sover} lrslib.c lrsmp.c
ln -s liblrsmp.so.%{ver} liblrsmp.so.%{sover}
ln -s liblrsmp.so.%{sover} liblrsmp.so

# Build the binaries against the GMP version of the library, except rat2float
gcc $CFLAGS -DGMP lrs.c -o lrs -L. -llrsgmp
gcc $CFLAGS -DGMP redund.c -o lrs-redund -L. -llrsgmp
gcc $CFLAGS -DGMP nash.c -o lrs-nash -L. -llrsgmp -lgmp
gcc $CFLAGS -DGMP fourier.c -o lrs-fourier -L. -llrsgmp -lgmp
gcc $CFLAGS -DGMP setupnash.c -o lrs-setupnash -L. -llrsgmp
gcc $CFLAGS -DGMP setupnash2.c -o lrs-setupnash2 -L. -llrsgmp
gcc $CFLAGS -DLRSMP rat2float.c -o lrs-rat2float -L. -llrsmp
gcc $CFLAGS float2rat.c -o lrs-float2rat
gcc $CFLAGS buffer.c -o lrs-buffer
gcc $CFLAGS 2gnash.c -o lrs-2gnash

%install
# Install the libraries
mkdir -p $RPM_BUILD_ROOT%{_libdir}
cp -a liblrs*.so* $RPM_BUILD_ROOT%{_libdir}

# Install the binaries
mkdir -p $RPM_BUILD_ROOT%{_bindir}
cp -p lrs lrs-* $RPM_BUILD_ROOT%{_bindir}

# Install the header files, but alter them to reflect 32-/64-bitness and fix
# up the include directives.
mkdir -p $RPM_BUILD_ROOT%{_includedir}/%{name}
if [ %{__isa_bits} = "64" ]; then
  sed -r -e 's|"(lrs.*\.h)"|<lrslib/\1>|' \
      -e "s|#include ARITH|#define B64\\n#include ARITH|" \
      lrslib.h > $RPM_BUILD_ROOT%{_includedir}/%{name}/lrslib.h
else
  sed -r 's|"(lrs.*\.h)"|<lrslib/\1>|' lrslib.h > \
      $RPM_BUILD_ROOT%{_includedir}/%{name}/lrslib.h
fi
touch -r lrslib.h $RPM_BUILD_ROOT%{_includedir}/%{name}/lrslib.h

sed -e 's|"gmp.h"|<gmp.h>|' lrsgmp.h > \
    $RPM_BUILD_ROOT%{_includedir}/%{name}/lrsgmp.h
touch -r lrsgmp.h $RPM_BUILD_ROOT%{_includedir}/%{name}/lrsgmp.h

cp -p lrslong.h lrsmp.h $RPM_BUILD_ROOT%{_includedir}/%{name}

# Install the man pages
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
cd man
for f in *.1; do
  sed "s/@VERSION@/%{upver}/" $f > $RPM_BUILD_ROOT%{_mandir}/man1/$f
  touch -r $f $RPM_BUILD_ROOT%{_mandir}/man1/$f
done

%files
%{_bindir}/lrs*
%{_mandir}/man1/lrs*

%files -n %{liblrs}
%doc COPYING readme
%{_libdir}/*.so.*

%files -n %{liblrs_devel}
%doc lrslib.html chdemo.c lpdemo.c vedemo.c
%{_includedir}/%{name}
%{_libdir}/*.so
