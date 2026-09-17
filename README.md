# QWRT AmneziaWG kernel build

Build AmneziaWG 3.1.20260906 for Xiaomi Mi Router BE7000 / QWRT 25.12.2.

Target kernel: 5.4.213
Target: ipq95xx/generic
Architecture: aarch64_cortex-a53

The build targets the QSDK 12.5 kernel tree and validates the external UDP-tunnel module dependencies during modpost, in addition to matching the router's exact kernel vermagic.
