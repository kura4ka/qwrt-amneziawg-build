#!/bin/sh
set -eu
KDIR="$1"
cd "$KDIR"
# QWRT 5.4.213 was built with PLTs disabled and module-tree lookup enabled.
# The public QSDK Kconfig resolves these differently, so patch generated config
# after syncconfig for external-module compilation.
sed -i '/^#define CONFIG_ARM64_MODULE_PLTS /d;/^#define CONFIG_MODULES_TREE_LOOKUP /d' include/generated/autoconf.h
echo '#define CONFIG_MODULES_TREE_LOOKUP 1' >> include/generated/autoconf.h
sed -i '/^CONFIG_ARM64_MODULE_PLTS=/d;/^# CONFIG_MODULES_TREE_LOOKUP is not set/d;/^CONFIG_MODULES_TREE_LOOKUP=/d' include/config/auto.conf
echo '# CONFIG_ARM64_MODULE_PLTS is not set' >> include/config/auto.conf
echo 'CONFIG_MODULES_TREE_LOOKUP=y' >> include/config/auto.conf
touch include/generated/autoconf.h include/config/auto.conf
