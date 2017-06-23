# TODO
# - consider a rust-std package containing .../rustlib/$target
#   This might allow multilib cross-compilation to work naturally.

# The channel can be stable, beta, or nightly
%define channel stable

#
# Conditional build:
%bcond_with bootstrap
%bcond_without	tests		# build without tests

%if "%{channel}" == "stable"
%define rustc_package rustc-%{version}-src
%else
%define rustc_package rustc-%{channel}-src
%endif

# To bootstrap from scratch, set the channel and date from src/stage0.txt
# e.g. 1.10.0 wants rustc: 1.9.0-2016-05-24
# or nightly wants some beta-YYYY-MM-DD
%define bootstrap_rust 1.17.0
%global bootstrap_cargo 0.18.0
%define bootstrap_date 2017-04-27
%define bootstrap_base https://static.rust-lang.org/dist/%{bootstrap_date}/rust-%{bootstrap_rust}

Summary:	The Rust Programming Language
Name:		rust
Version:	1.18.0
Release:	0.1
License:	(ASL 2.0 or MIT) and (BSD and ISC and MIT)
# ^ written as: (rust itself) and (bundled libraries)
Group:		Development/Languages
Source0:	https://static.rust-lang.org/dist/%{rustc_package}.tar.gz
# Source0-md5:	c37c0cd9d500f6a9d1f2f44401351f88
Source1:	%{bootstrap_base}-x86_64-unknown-linux-gnu.tar.gz
# Source1-md5:	98e8f479515969123b4c203191104a54
Source2:	%{bootstrap_base}-i686-unknown-linux-gnu.tar.gz
# Source2-md5:	2d5de850c32aa8d40c8c21abacf749f8
URL:		https://www.rust-lang.org/
BuildRequires:	cmake
BuildRequires:	curl
BuildRequires:	gcc
BuildRequires:	libstdc++-devel
BuildRequires:	llvm-devel
BuildRequires:	python
BuildRequires:	zlib-devel
%if %{without bootstrap}
BuildRequires:  cargo >= %{bootstrap_cargo}
BuildRequires:	%{name} < %{version}-%{release}
BuildRequires:	%{name} >= %{bootstrap_rust}
%endif
# make check needs "ps" for src/test/run-pass/wait-forked-but-failed-child.rs
BuildRequires:	procps
# TODO: work on unbundling these!
Provides:	bundled(hoedown) = 3.0.5
Provides:	bundled(jquery) = 2.1.4
Provides:	bundled(libbacktrace) = 6.1.0
Provides:	bundled(miniz) = 1.14
# The C compiler is needed at runtime just for linking.  Someday rustc might
# invoke the linker directly, and then we'll only need binutils.
# https://github.com/rust-lang/rust/issues/11937
Requires:	gcc
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)
# Only x86_64 and i686 are Tier 1 platforms at this time.
# https://doc.rust-lang.org/stable/book/getting-started.html#tier-1
ExclusiveArch:	%{x8664} %{ix86} %{arm}

%define rust_triple %{_target_cpu}-unknown-linux-gnu

%if %{without bootstrap}
%define local_rust_root %{_prefix}
%else
%define bootstrap_root rust-%{bootstrap_rust}-%{rust_triple}
%define local_rust_root %{_builddir}/%{rustc_package}/%{bootstrap_root}
%endif

# ALL Rust libraries are private, because they don't keep an ABI.
%global _privatelibs lib.*-[[:xdigit:]]{8}[.]so.*
%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

%description
Rust is a systems programming language that runs blazingly fast,
prevents segfaults, and guarantees thread safety.

This package includes the Rust compiler, standard library, and
documentation generator.

%package gdb
Summary:	GDB pretty printers for Rust
Requires:	gdb
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description gdb
This package includes the rust-gdb script, which allows easier
debugging of Rust programs.

%package doc
Summary:	Documentation for Rust
# NOT BuildArch:      noarch
# Note, while docs are mostly noarch, some things do vary by target_arch.
# Koji will fail the build in rpmdiff if two architectures build a noarch
# subpackage differently, so instead we have to keep its arch.

%description doc
This package includes HTML documentation for the Rust programming
language and its standard library.

%prep
%setup -q -n %{rustc_package}
%if %{with bootstrap}
%ifarch %{x8664}
tar xf %{SOURCE1}
%endif
%ifarch %{ix86}
tar xf %{SOURCE2}
%endif
%{__mv} %{bootstrap_root} %{bootstrap_root}-root
%{bootstrap_root}-root/install.sh \
	--components=cargo,rustc,rust-std-%{rust_triple} \
	--prefix=%{local_rust_root} \
	--disable-ldconfig
test -f %{local_rust_root}/bin/cargo
test -f %{local_rust_root}/bin/rustc
%endif

# unbundle
rm -r src/jemalloc/
rm -r src/llvm/

# extract bundled licenses for packaging
cp -p src/rt/hoedown/LICENSE src/rt/hoedown/LICENSE-hoedown
sed -e '/*\//q' src/libbacktrace/backtrace.h \
	>src/libbacktrace/LICENSE-libbacktrace

# rust-gdb has hardcoded SYSROOT/lib -- let's make it noarch
sed -i -e 's#DIRECTORY=".*"#DIRECTORY="%{_datadir}/%{name}/etc"#' \
	src/etc/rust-gdb

# These tests assume that alloc_jemalloc is present
sed -i -e '1i // ignore-test jemalloc is disabled' \
	src/test/compile-fail/allocator-dylib-is-system.rs \
	src/test/compile-fail/allocator-rust-dylib-is-jemalloc.rs \
	src/test/run-pass/allocator-default.rs

# Fedora's LLVM doesn't support any mips targets -- see "llc -version".
# Fixed properly by Rust PR36344, which should be released in 1.13.
sed -i -e '/target=mips/,+1s/^/# unsupported /' \
	src/test/run-make/atomic-lock-free/Makefile

%if %{without bootstrap}
# The hardcoded stage0 "lib" is inappropriate when using Fedora's own rustc
sed -i -e '/^HLIB_RELATIVE/s/lib$/$$(CFG_LIBDIR_RELATIVE)/' mk/main.mk
%endif

%build
%configure \
	--disable-option-checking \
	--build=%{rust_triple} --host=%{rust_triple} --target=%{rust_triple} \
	--enable-local-rust --local-rust-root=%{local_rust_root} \
	--llvm-root=%{_prefix} --disable-codegen-tests \
	--disable-jemalloc \
	--disable-rpath \
	--enable-debuginfo \
	--enable-vendor \
	--release-channel=%{channel}

./x.py dist

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	VERBOSE=1 \
	DESTDIR=$RPM_BUILD_ROOT

# Remove installer artifacts (manifests, uninstall scripts, etc.)
find $RPM_BUILD_ROOT%{_libdir}/rustlib/ -maxdepth 1 -type f -exec rm -v '{}' '+'

# We don't want to ship the target shared libraries for lack of any Rust ABI.
find $RPM_BUILD_ROOT%{_libdir}/rustlib/ -type f -name '*.so' -exec rm -v '{}' '+'

# The remaining shared libraries should be executable for debuginfo extraction.
find $RPM_BUILD_ROOT%{_libdir}/ -type f -name '*.so' -exec chmod -v +x '{}' '+'

# They also don't need the .rustc metadata anymore, so they won't support linking.
# (but direct section removal breaks dynamic symbols -- leave it for now...)
#find $RPM_BUILD_ROOT/%{_libdir}/ -type f -name '*.so' -exec objcopy -R .rustc '{}' ';'

# FIXME: __os_install_post will strip the rlibs
# -- should we find a way to preserve debuginfo?

# Remove unwanted documentation files (we already package them)
rm $RPM_BUILD_ROOT%{_docdir}/%{name}/README.md
rm $RPM_BUILD_ROOT%{_docdir}/%{name}/COPYRIGHT
rm $RPM_BUILD_ROOT%{_docdir}/%{name}/LICENSE-APACHE
rm $RPM_BUILD_ROOT%{_docdir}/%{name}/LICENSE-MIT

# Sanitize the HTML documentation
find $RPM_BUILD_ROOT%{_docdir}/%{name}/html -empty -delete
find $RPM_BUILD_ROOT%{_docdir}/%{name}/html -type f -exec chmod -x '{}' '+'

# Move rust-gdb's python scripts so they're noarch
install -d $RPM_BUILD_ROOT%{_datadir}/%{name}
mv -v $RPM_BUILD_ROOT%{_libdir}/rustlib%{_sysconfdir} $RPM_BUILD_ROOT%{_datadir}/%{name}/

%clean
rm -rf $RPM_BUILD_ROOT

%post	-p /sbin/ldconfig
%postun	-p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc COPYRIGHT LICENSE-APACHE LICENSE-MIT
%doc src/libbacktrace/LICENSE-libbacktrace
%doc src/rt/hoedown/LICENSE-hoedown
%doc README.md
%attr(755,root,root) %{_bindir}/rustc
%attr(755,root,root) %{_bindir}/rustdoc
%{_mandir}/man1/rustc.1*
%{_mandir}/man1/rustdoc.1*
%{_libdir}/lib*
%dir %{_libdir}/rustlib
%{_libdir}/rustlib/%{rust_triple}

%files gdb
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/rust-gdb
%{_datadir}/%{name}

%files doc
%defattr(644,root,root,755)
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/html/FiraSans-LICENSE.txt
%doc %{_docdir}/%{name}/html/Heuristica-LICENSE.txt
%doc %{_docdir}/%{name}/html/LICENSE-APACHE.txt
%doc %{_docdir}/%{name}/html/LICENSE-MIT.txt
%doc %{_docdir}/%{name}/html/SourceCodePro-LICENSE.txt
%doc %{_docdir}/%{name}/html/SourceSerifPro-LICENSE.txt
%doc %{_docdir}/%{name}/html/
