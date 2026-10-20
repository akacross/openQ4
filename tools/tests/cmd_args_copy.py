#!/usr/bin/env python3
"""Copies of idCmdArgs must keep their arguments, including inside idList.

idCmdArgs::argv points into the object's own tokenized buffer, which
operator= re-points. idList::Append copies its argument before growing the
list, so idCmdArgs needs a copy constructor that does the same: with the
implicit member-wise copy, the queued command that lands on a list growth
kept argv aimed at the caller's buffer, and operator= then turned that into
an unrelated offset. Startup commands are queued in an idList<idCmdArgs>, so
the 17th "+" command on a command line silently lost its text -- the
dedicated-server smokes never ran their "+quit".

This compiles the production idCmdArgs header with its operator= and
AppendArg bodies against idList, queues commands past several growths, and
checks every one -- and a copy-constructed one -- still reads back intact.
"""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from filesystem_case_segments import function_body

ROOT = Path(__file__).resolve().parents[2]

SUPPORT = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#define ID_INLINE inline
#define MAX_STRING_CHARS 1024
struct idStr {
	static void Copynz( char *dest, const char *src, int destsize ) {
		std::strncpy( dest, src, destsize - 1 );
		dest[ destsize - 1 ] = 0;
	}
};
struct idLib {
	static int SizeToInt( size_t value, const char * ) { return static_cast<int>( value ); }
};
#include "src/idlib/containers/List.h"
#include "src/idlib/CmdArgs.h"
'''

MAIN = r'''
static idCmdArgs Command( int index ) {
	idCmdArgs args;
	args.AppendArg( "cmd" );
	args.AppendArg( std::to_string( index ).c_str() );
	return args;
}

static bool Intact( const idCmdArgs &args, int index ) {
	return args.Argc() == 2 && std::strcmp( args.Argv( 0 ), "cmd" ) == 0 &&
		std::strcmp( args.Argv( 1 ), std::to_string( index ).c_str() ) == 0;
}

int main() {
	int failures = 0;
	const idCmdArgs source = Command( 7 );
	const idCmdArgs copied( source );
	if ( !Intact( copied, 7 ) ) {
		std::fprintf( stderr, "copy-constructed idCmdArgs lost its arguments\n" );
		++failures;
	}

	// The startup queue: one Append per "+" command, growing every 16.
	idList<idCmdArgs> queue;
	for ( int i = 0; i < 40; ++i ) {
		const idCmdArgs args = Command( i );
		queue.Append( args );
	}
	for ( int i = 0; i < 40; ++i ) {
		if ( !Intact( queue[ i ], i ) ) {
			std::fprintf( stderr, "queued command %d lost its arguments\n", i );
			++failures;
		}
	}
	// Drain it the way ExecuteCommandBuffer does.
	for ( int i = 0; i < 40; ++i ) {
		idCmdArgs next;
		next = queue[ 0 ];
		queue.RemoveIndex( 0 );
		if ( !Intact( next, i ) ) {
			std::fprintf( stderr, "drained command %d lost its arguments\n", i );
			++failures;
		}
	}
	return failures ? 1 : 0;
}
'''


def main() -> None:
    header = (ROOT / "src/idlib/CmdArgs.h").read_text(encoding="utf-8")
    if "idCmdArgs( const idCmdArgs &args ) { argc = 0; *this = args; }" not in header:
        raise AssertionError("idCmdArgs must copy-construct through operator= so argv is re-pointed")
    source = (ROOT / "src/idlib/CmdArgs.cpp").read_text(encoding="utf-8")
    code = SUPPORT + "\n".join(function_body(source, signature) for signature in (
        "void idCmdArgs::operator=( const idCmdArgs &args )",
        "void idCmdArgs::AppendArg( const char *text )",
    )) + MAIN

    compiler = next((found for name in ("clang++", "g++", "c++") if (found := shutil.which(name))), None)
    if not compiler:
        raise RuntimeError("C++ compiler required")
    (ROOT / ".tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmd-args-copy-", dir=ROOT / ".tmp") as temp:
        env = dict(os.environ, TEMP=temp, TMP=temp)
        test_source = Path(temp) / "cmd_args_copy.cpp"
        test_source.write_text(code, encoding="utf-8")
        binary = Path(temp) / "cmd_args_copy.exe"
        subprocess.run([compiler, "-std=c++17", "-I", str(ROOT), str(test_source), "-o", str(binary)], check=True, env=env)
        subprocess.run([str(binary)], check=True, env=env)
    print("cmd_args_copy: ok")


if __name__ == "__main__":
    main()
