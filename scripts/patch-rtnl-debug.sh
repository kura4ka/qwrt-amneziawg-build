#!/bin/sh
set -eu
python3 - <<'PY'
from pathlib import Path
p=Path("awg/src/device.c")
s=p.read_text()

if "AWGDBG: NEWLINK_ENTER" not in s:
    anchor='\tstruct wg_device *wg = netdev_priv(dev);\n\tint ret = -ENOMEM, i;'
    if anchor not in s:
        raise SystemExit("wg_newlink declarations anchor not found")
    s=s.replace(anchor, anchor+'\n\tpr_err("AWGDBG: NEWLINK_ENTER dev=%px name=%s\\n", dev, dev ? dev->name : "<null>");',1)

if "AWGDBG: NEWLINK_STEP register_netdevice" not in s:
    old='\tret = register_netdevice(dev);'
    new='\tpr_err("AWGDBG: NEWLINK_STEP register_netdevice\\n");\n\tret = register_netdevice(dev);\n\tpr_err("AWGDBG: NEWLINK_REGISTER_RET=%d\\n", ret);'
    if old not in s:
        raise SystemExit("register_netdevice anchor not found")
    s=s.replace(old,new,1)

if "AWGDBG: NEWLINK_SUCCESS" not in s:
    old='\tpr_debug("%s: Interface created\\n", dev->name);'
    new='\tpr_err("AWGDBG: NEWLINK_SUCCESS name=%s\\n", dev->name);\n\tpr_debug("%s: Interface created\\n", dev->name);'
    if old not in s:
        raise SystemExit("success anchor not found")
    s=s.replace(old,new,1)

p.write_text(s)
PY
