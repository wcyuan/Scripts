#
# Scratch Makefile, no project -- looks for any source file
#
# Gnu Make Reference:
#	http://www.gnu.org/manual/make-3.77/html_mono/make.html
#   Automatic Variables:
#	http://www.gnu.org/manual/make/html_chapter/make_10.html#SEC97
#
# each project should
#	be written in C or C++
# 	have a unique name
#	be composed of only 1 source file
#	source file should have the same name with a suffix
#	.c for C, .cc for C++
#	.cpp for top coder
#	be easily replaceable
#
# 						    7/27/99
###########################################################

CC 		= gcc
CXX 		= g++
#CXX 		= CC

INCLUDE 	= -I.

# Lots of warnings
CFLAGS		= -Wall -ansi -pedantic
# I have no idea what this flag does
#CFLAGS		+= -z
# Enable Debugging
CFLAGS		+= -g
# Optimize
CFLAGS		+= -O
# Enable Profiling
#CFLAGS		+= -pg

TCL_ROOT=	/prod/tools/packages/tcl-8.3-mt
TOOLS_ROOT=	/prod/tools/packages
X_ROOT=		/usr/local/X
SYB_ROOT=	/usr/local/sybase
LOCLIB_ROOT=    /usr/local/lib
RW_ROOT =	/prod/tools/packages/rogue

CXXFLAGS 	= -g
# these flags add some nice warnings, but they also add annoying
# warnings about iostream
#CXXFLAGS	+= +w +w2
#CXXFLAGS	+= -instances=explicit
#CXXFLAGS	+= -library=rwtools7_std
CXXFLAGS 	+= -I$(TOOLS_ROOT)/include
CXXFLAGS	+= -I$(TCL_ROOT)/include
CXXFLAGS	+= -I$(X_ROOT)/include
CXXFLAGS	+= -I$(SYB_ROOT)/include
CXXFLAGS	+= -I$(RW_ROOT)
CXXFLAGS	+= -I$(GUAS_ROOT)/include -I/usr/include

LDFLAGS		= -lm
LIBS		=

CINCLUDE	= $(INCLUDE) -include cinclude.h
#CXXINCLUDE	= $(INCLUDE) -include cxxinclude.h
#CXXINCLUDE	= $(INCLUDE) -I/u/gneppa/usr/include/stl
CXXINCLUDE	= $(INCLUDE)

CSOURCE		= $(wildcard *.c)
CXXSOURCE1	= $(wildcard *.cc)
CXXSOURCE2	= $(wildcard *.cpp)
CXXSOURCE	= $(CXXSOURCE1) $(CXXSOURCE2)
SOURCES		= $(CSOURCE) $(CXXSOURCE)

CEXE		= $(CSOURCE:.c=)
CXXEXE1		= $(CXXSOURCE1:.cc=)
CXXEXE2		= $(CXXSOURCE2:.cpp=)
CXXEXE		= $(CXXEXE1) $(CXXEXE2)
BINARIES	= $(CEXE) $(CXXEXE) a.out


# old suffix rule
.SUFFIXES : .o .c .cpp .s

# first target is the default with no argument
default:
	@echo "No default target for this Makefile"

all:	$(BINARIES)

%.o: 	%.c
	$(CC) -c $(CFLAGS) $(CINCLUDE) $(LDFLAGS) $(LIBS) $< -o $@
%.o: 	%.cc
	$(CXX) -c $(CXXFLAGS) $(CXXINCLUDE) $(LDFLAGS) $(LIBS) $< -o $@

# Implicitly defined, but include them anyway
%:: 	%.c
	$(CC) $(CFLAGS) $(CINCLUDE) $(LDFLAGS) $(LIBS) $< -o $@
%:: 	%.cc
	$(CXX) $(CXXFLAGS) $(CXXINCLUDE) $(LDFLAGS) $(LIBS) $< -o $@
%:: 	%.C
	$(CXX) $(CXXFLAGS) $(CXXINCLUDE) $(LDFLAGS) $(LIBS) $< -o $@
%:: 	%.cpp
	$(CXX) $(CXXFLAGS) $(CXXINCLUDE) $(LDFLAGS) $(LIBS) $< -o $@

# .PHONY targets run regardless of last modification
.PHONY:	clean submit sprint all print clobber default

# the - before the command means to ignore errors
clean: ; -rm -f *.o core *~

# the - before the command means to ignore errors
clobber: clean
	-rm -f $(BINARIES) *~

# no printing right now
sprint: ; # enscript -2rG -d $PRINTER $(SOURCES)

#test:
#	@echo $(filter %.cc, $(CXXSOURCE))
#	@echo $(filter %.cpp, $(CXXSOURCE))
#	@echo $((filter %.cc, $(CXXSOURCE)):.cc=)
#	@echo $((filter %.cpp, $(CXXSOURCE)):.cpp=)
#	@echo $(CXXEXE)
#	@echo $(CXXSOURCE:.cc=)
#	@echo "Binaries =" $(BINARIES)
#	@echo "Sources =" $(SOURCES)
