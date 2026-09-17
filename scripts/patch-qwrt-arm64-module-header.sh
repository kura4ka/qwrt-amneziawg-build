#!/bin/sh
set -eu
KDIR="$1"
FILE="$KDIR/arch/arm64/include/asm/module.h"
python3 - "$FILE" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = '''#ifdef CONFIG_ARM64_MODULE_PLTS
struct mod_plt_sec {
\tint\t\t\tplt_shndx;
\tint\t\t\tplt_num_entries;
\tint\t\t\tplt_max_entries;
};

struct mod_arch_specific {
\tstruct mod_plt_sec\tcore;
\tstruct mod_plt_sec\tinit;

\t/* for CONFIG_DYNAMIC_FTRACE */
\tstruct plt_entry \t*ftrace_trampoline;
};
#endif
'''
new = '''#ifdef CONFIG_ARM64_MODULE_PLTS
struct mod_plt_sec {
\tint\t\t\tplt_shndx;
\tint\t\t\tplt_num_entries;
\tint\t\t\tplt_max_entries;
};
#endif

#ifdef CONFIG_HAVE_MOD_ARCH_SPECIFIC
struct mod_arch_specific {
#ifdef CONFIG_ARM64_MODULE_PLTS
\tstruct mod_plt_sec\tcore;
\tstruct mod_plt_sec\tinit;

\t/* for CONFIG_DYNAMIC_FTRACE */
\tstruct plt_entry \t*ftrace_trampoline;
#endif
};
#endif
'''
if old not in s:
    raise SystemExit('expected ARM64 module header block not found')
p.write_text(s.replace(old, new, 1))
PY
