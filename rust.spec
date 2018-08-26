# TODO
# - consider a rust-std package containing .../rustlib/$target
#   This might allow multilib cross-compilation to work naturally.
#
# Conditional build:
%bcond_with	bootstrap	# bootstrap using precompiled binaries
%bcond_without	full_debuginfo	# full debuginfo vs only std debuginfo (full takes gigabytes of memory to build)
%bcond_without	system_llvm	# system LLVM
%bcond_with	tests		# build without tests

# The channel can be stable, beta, or nightly
%define		channel		stable

%if "%{channel}" == "stable"
%define		rustc_package	rustc-%{version}-src
%else
%define		rustc_package	rustc-%{channel}-src
%endif

# To bootstrap from scratch, set the channel and date from src/stage0.txt
# e.g. 1.10.0 wants rustc: 1.9.0-2016-05-24
# or nightly wants some beta-YYYY-MM-DD
%define		bootstrap_rust	1.27.2
%define		bootstrap_cargo	1.27.0
%define		bootstrap_date	2018-07-20

Summary:	The Rust Programming Language
Summary(pl.UTF-8):	Język programowania Rust
Name:		rust
Version:	1.28.0
Release:	1
# Licenses: (rust itself) and (bundled libraries)
License:	(Apache v2.0 or MIT) and (BSD and ISC and MIT)
Group:		Development/Languages
Source0:	https://static.rust-lang.org/dist/%{rustc_package}.tar.gz
# Source0-md5:	80acd625df9389e16a88fc4f1d0f646b
Source1:	https://static.rust-lang.org/dist/%{bootstrap_date}/rust-%{bootstrap_rust}-x86_64-unknown-linux-gnu.tar.gz
# Source1-md5:	3564263497f7b3cb0c9391f7b0c5831d
Source2:	https://static.rust-lang.org/dist/%{bootstrap_date}/rust-%{bootstrap_rust}-i686-unknown-linux-gnu.tar.gz
# Source2-md5:	5df2caf50f5e8c4706d8151ebd845f9c
Patch0:		x32.patch
URL:		https://www.rust-lang.org/
# for src/compiler-rt
BuildRequires:	cmake >= 3.4.3
BuildRequires:	curl
BuildRequires:	libstdc++-devel
%{?with_system_llvm:BuildRequires:	llvm-devel}
BuildRequires:	ncurses-devel
BuildRequires:	python >= 1:2.7
BuildRequires:	zlib-devel
%if %{without bootstrap}
BuildRequires:	%{name} >= %{bootstrap_rust}
BuildRequires:	cargo >= %{bootstrap_cargo}
BuildConflicts:	%{name} > %{version}
%endif
# make check needs "ps" for src/test/run-pass/wait-forked-but-failed-child.rs
BuildRequires:	procps
# The C compiler is needed at runtime just for linking.  Someday rustc might
# invoke the linker directly, and then we'll only need binutils.
# https://github.com/rust-lang/rust/issues/11937
Requires:	gcc
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)
# Only x86_64 and i686 are Tier 1 platforms at this time.
# https://doc.rust-lang.org/stable/book/getting-started.html#tier-1
ExclusiveArch:	%{x8664} %{ix86} x32

%ifarch x32
%define		rust_triple	x86_64-unknown-linux-gnux32
%else
%define		rust_triple	%{_target_cpu}-unknown-linux-gnu
%endif

%if %{without bootstrap}
%define		local_rust_root	%{_prefix}
%else
%define		bootstrap_root	rust-%{bootstrap_rust}-%{rust_triple}
%define		local_rust_root	%{_builddir}/%{rustc_package}/%{bootstrap_root}
%endif

# We're going to override --libdir when configuring to get rustlib into a
# common path, but we'll fix the shared libraries during install.
# Without this ugly hack, rust would not be able to build itself
# for non-bootstrap build, lib64 is just too complicated for it.
%define		common_libdir	%{_prefix}/lib
%define		rustlibdir	%{common_libdir}/rustlib

# once_call/once_callable non-function libstdc++ symbols
%define		skip_post_check_so	'librustc.*llvm.*\.so.*'

# ALL Rust libraries are private, because they don't keep an ABI.
%define		_noautoreqfiles		lib.*-[[:xdigit:]]{8}[.]so.*
%define		_noautoprovfiles	lib.*-[[:xdigit:]]{8}[.]so.*

%description
Rust is a systems programming language that runs blazingly fast,
prevents segfaults, and guarantees thread safety.

This package includes the Rust compiler, standard library, and
documentation generator.

%description -l pl.UTF-8
Rust to systemowy język programowania działający bardzo szybko,
zapobiegający naruszeniom ochrony pamięci i gwarantujący
bezpieczną wielowątkowość.

%package debugger-common
Summary:	Common debugger pretty printers for Rust
Summary(pl.UTF-8):	Narzędzia wypisujące struktury Rusa wspólne dla różnych debuggerów
Group:		Development/Debuggers
BuildArch:	noarch

%description debugger-common
This package includes the common functionality for rust-gdb and
rust-lldb.

%description debugger-common -l pl.UTF-8
Ten pakiet zawiera wspólny kod dla pakietów rust-gdb i rust-lldb.

%package gdb
Summary:	GDB pretty printers for Rust
Summary(pl.UTF-8):	Ładne wypisywanie struktur Rusta w GDB
Group:		Development/Debuggers
Requires:	%{name}-debugger-common = %{version}-%{release}
Requires:	gdb
BuildArch:	noarch

%description gdb
This package includes the rust-gdb script, which allows easier
debugging of Rust programs.

%description gdb -l pl.UTF-8
Ten pakiet zawiera skrypt rust-gdb, pozwalający na łatwiejsze
odpluskwianie programów w języku Rust.

%package lldb
Summary:	LLDB pretty printers for Rust
Summary(pl.UTF-8):	Ładne wypisywanie struktur Rusta w LLDB
Group:		Development/Debuggers
Requires:	%{name}-debugger-common = %{version}-%{release}
Requires:	lldb
BuildArch:	noarch

%description lldb
This package includes the rust-lldb script, which allows easier
debugging of Rust programs.

%description lldb -l pl.UTF-8
Ten pakiet zawiera skrypt rust-lldb, pozwalający na łatwiejsze
odpluskwianie programów w języku Rust.

%package doc
Summary:	Documentation for Rust
Summary(pl.UTF-8):	Dokumentacja do Rusta
Group:		Documentation
BuildArch:	noarch

%description doc
This package includes HTML documentation for the Rust programming
language and its standard library.

%description doc -l pl.UTF-8
Ten pakiet zawiera dokumentację w formacie HTML do języka
programowania Rust i jego biblioteki standardowej.

%prep
%setup -q -n %{rustc_package}
%ifarch x32
%patch0 -p1
%endif

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
# We're disabling jemalloc, but rust-src still wants it.
#%{__rm} -r src/jemalloc
%{?with_system_llvm:%{__rm} -r src/llvm}

# extract bundled licenses for packaging
sed -e '/*\//q' src/libbacktrace/backtrace.h \
	>src/libbacktrace/LICENSE-libbacktrace

# rust-gdb has hardcoded SYSROOT/lib -- let's make it noarch
sed -i -e 's#DIRECTORY=".*"#DIRECTORY="%{_datadir}/%{name}/etc"#' \
	src/etc/rust-gdb

# The configure macro will modify some autoconf-related files, which upsets
# cargo when it tries to verify checksums in those files.  If we just truncate
# that file list, cargo won't have anything to complain about.
find src/vendor -name .cargo-checksum.json \
	-exec sed -i.uncheck -e 's/"files":{[^}]*}/"files":{ }/' '{}' '+'

%build
%configure \
	--build=%{rust_triple} \
	--host=%{rust_triple} \
	--target=%{rust_triple} \
	--libdir=%{common_libdir} \
	--disable-codegen-tests \
	--disable-jemalloc \
	--disable-option-checking \
	--disable-rpath \
	--disable-debuginfo-lines \
%if %{with full_debuginfo}
	--disable-debuginfo-only-std \
	--enable-debuginfo \
%else
	--enable-debuginfo-only-std \
	--disable-debuginfo \
%endif
	--enable-llvm-link-shared \
	--local-rust-root=%{local_rust_root} \
	--enable-vendor \
	--llvm-root=%{_prefix} \
	--release-channel=%{channel}

RUST_BACKTRACE=full \
./x.py dist

%{?with_tests:./x.py test}

%install
rm -rf $RPM_BUILD_ROOT

DESTDIR=$RPM_BUILD_ROOT ./x.py install
DESTDIR=$RPM_BUILD_ROOT ./x.py install src

# Make sure the shared libraries are in the proper libdir
%if "%{_libdir}" != "%{common_libdir}"
mkdir -p %{buildroot}%{_libdir}
find $RPM_BUILD_ROOT%{common_libdir} -maxdepth 1 -type f -name '*.so' \
	-exec mv -v -t $RPM_BUILD_ROOT%{_libdir} '{}' '+'
%endif

# The shared libraries should be executable for debuginfo extraction.
find $RPM_BUILD_ROOT%{_libdir}/ -type f -name '*.so' -exec chmod -v +x '{}' '+'

# The libdir libraries are identical to those under rustlib/.  It's easier on
# library loading if we keep them in libdir, but we do need them in rustlib/
# to support dynamic linking for compiler plugins, so we'll symlink.
(cd "$RPM_BUILD_ROOT%{rustlibdir}/%{rust_triple}/lib" &&
	find ../../../../%{_lib} -maxdepth 1 -name '*.so' \
	-exec ln -v -f -s -t . '{}' '+')

# Remove installer artifacts (manifests, uninstall scripts, etc.)
find $RPM_BUILD_ROOT%{rustlibdir}/ -maxdepth 1 -type f -exec rm -v '{}' '+'

# FIXME: __os_install_post will strip the rlibs
# -- should we find a way to preserve debuginfo?

# Remove unwanted documentation files (we already package them)
%{__rm} $RPM_BUILD_ROOT%{_docdir}/%{name}/README.md
%{__rm} $RPM_BUILD_ROOT%{_docdir}/%{name}/COPYRIGHT
%{__rm} $RPM_BUILD_ROOT%{_docdir}/%{name}/LICENSE-APACHE
%{__rm} $RPM_BUILD_ROOT%{_docdir}/%{name}/LICENSE-MIT

# Sanitize the HTML documentation
find $RPM_BUILD_ROOT%{_docdir}/%{name}/html -empty -delete
find $RPM_BUILD_ROOT%{_docdir}/%{name}/html -type f -exec chmod -x '{}' '+'

# Move rust-gdb's python scripts so they're noarch
install -d $RPM_BUILD_ROOT%{_datadir}/%{name}
%{__mv} $RPM_BUILD_ROOT%{rustlibdir}/etc $RPM_BUILD_ROOT%{_datadir}/%{name}

# We don't need stdlib source
%{__rm} -r $RPM_BUILD_ROOT%{rustlibdir}/src

%clean
rm -rf $RPM_BUILD_ROOT

%post	-p /sbin/ldconfig
%postun	-p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc COPYRIGHT LICENSE-APACHE LICENSE-MIT README.md src/libbacktrace/LICENSE-libbacktrace
%attr(755,root,root) %{_bindir}/rustc
%attr(755,root,root) %{_bindir}/rustdoc
%attr(755,root,root) %{_libdir}/libarena-*.so
%attr(755,root,root) %{_libdir}/libfmt_macros-*.so
%attr(755,root,root) %{_libdir}/libgraphviz-*.so
%attr(755,root,root) %{_libdir}/libproc_macro-*.so
%attr(755,root,root) %{_libdir}/librustc*-*.so
%attr(755,root,root) %{_libdir}/libserialize-*.so
%attr(755,root,root) %{_libdir}/libstd-*.so
%attr(755,root,root) %{_libdir}/libsyntax-*.so
%attr(755,root,root) %{_libdir}/libsyntax_ext-*.so
%attr(755,root,root) %{_libdir}/libsyntax_pos-*.so
%attr(755,root,root) %{_libdir}/libterm-*.so
%attr(755,root,root) %{_libdir}/libtest-*.so
%{_mandir}/man1/rustc.1*
%{_mandir}/man1/rustdoc.1*
%dir %{rustlibdir}
%dir %{rustlibdir}/%{rust_triple}
%dir %{rustlibdir}/%{rust_triple}/codegen-backends
%attr(755,root,root) %{rustlibdir}/%{rust_triple}/codegen-backends/*.so
%dir %{rustlibdir}/%{rust_triple}/lib
%attr(755,root,root) %{rustlibdir}/%{rust_triple}/lib/*.so
%{rustlibdir}/%{rust_triple}/lib/*.rlib

%files debugger-common
%defattr(644,root,root,755)
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/etc
%{_datadir}/%{name}/etc/debugger_*.py*

%files lldb
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/rust-lldb
%{_datadir}/%{name}/etc/lldb_*.py*

%files gdb
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/rust-gdb
%{_datadir}/%{name}/etc/gdb_*.py*

%files doc
%defattr(644,root,root,755)
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/html
