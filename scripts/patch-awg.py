from pathlib import Path

p = Path('awg/src/compat/compat.h')
s = p.read_text()
s = s.replace(
    ' && !defined(ISUBUNTU2004)\n#define COMPAT_INIT_CRYPTO',
    ' && !defined(ISUBUNTU2004) && !defined(ISQSDK)\n#define COMPAT_INIT_CRYPTO', 1)
s = s.replace(
    '#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 16, 0)\n#include <crypto/chacha.h>',
    '#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 16, 0)\n#if defined(ISQSDK) && LINUX_VERSION_CODE < KERNEL_VERSION(5, 5, 0)\n#include "crypto/chacha/include/crypto/chacha.h"\n#else\n#include <crypto/chacha.h>\n#endif', 1)
s = s.replace('(CHACHA_BLOCK_SIZE / sizeof(u32))', '(CHACHA20_BLOCK_SIZE / sizeof(u32))', 1)
s = s.replace(
    '#include <crypto/blake2s.h>\n#define blake2s_ctx blake2s_state\n#define blake2s(key, keylen, in, inlen, out, outlen) \\\n\tblake2s(out, in, key, outlen, inlen, keylen)',
    '#include <zinc/blake2s.h>\n#define blake2s_ctx blake2s_state', 1)
p.write_text(s)

p = Path('awg/src/noise.c')
s = p.read_text().replace(
    'blake2s(NULL, 0, handshake_name, sizeof(handshake_name),\n\t\thandshake_init_chaining_key, NOISE_HASH_LEN);',
    'blake2s(handshake_init_chaining_key, handshake_name, NULL,\n\t\tNOISE_HASH_LEN, sizeof(handshake_name), 0);', 1)
p.write_text(s)

p = Path('awg/src/cookie.c')
s = p.read_text()
s = s.replace('blake2s(key, NOISE_SYMMETRIC_KEY_LEN, message, len, mac1, COOKIE_LEN);', 'blake2s(mac1, message, key, COOKIE_LEN, len, NOISE_SYMMETRIC_KEY_LEN);', 1)
s = s.replace('blake2s(cookie, COOKIE_LEN, message, len, mac2, COOKIE_LEN);', 'blake2s(mac2, message, cookie, COOKIE_LEN, len, COOKIE_LEN);', 1)
s = s.replace('#include <crypto/blake2s.h>', '#include <zinc/blake2s.h>', 1)
p.write_text(s)

p = Path('awg/src/messages.h')
p.write_text(p.read_text().replace('#include <crypto/blake2s.h>', '#include <zinc/blake2s.h>', 1))

p = Path('awg/src/compat/crypto/chacha/include/crypto/chacha.h')
s = p.read_text().replace('#ifndef _CRYPTO_CHACHA_H', '#ifndef __AWG_COMPAT_CRYPTO_CHACHA_H', 1)
s = s.replace('#define _CRYPTO_CHACHA_H', '#define __AWG_COMPAT_CRYPTO_CHACHA_H', 1)
s = s.replace('#endif /* _CRYPTO_CHACHA_H */', '#endif /* __AWG_COMPAT_CRYPTO_CHACHA_H */', 1)
p.write_text(s)

p = Path('awg/src/main.c')
s = p.read_text()
s = s.replace(
    'static int __init wg_mod_init(void)\n{\n\tint ret;\n',
    'static int __init wg_mod_init(void)\n{\n\tint ret;\n\tpr_err("AWGDBG: init start\\n");\n', 1)
s = s.replace(
    '\tret = wg_allowedips_slab_init();\n\tif (ret < 0)\n\t\tgoto err_allowedips;',
    '\tret = wg_allowedips_slab_init();\n\tpr_err("AWGDBG: allowedips_slab_init=%d\\n", ret);\n\tif (ret < 0)\n\t\tgoto err_allowedips;', 1)
s = s.replace(
    '\tret = wg_peer_init();\n\tif (ret < 0)\n\t\tgoto err_peer;',
    '\tret = wg_peer_init();\n\tpr_err("AWGDBG: peer_init=%d\\n", ret);\n\tif (ret < 0)\n\t\tgoto err_peer;', 1)
s = s.replace(
    '\tret = wg_device_init();\n\tif (ret < 0)\n\t\tgoto err_device;',
    '\tret = wg_device_init();\n\tpr_err("AWGDBG: device_init=%d\\n", ret);\n\tif (ret < 0)\n\t\tgoto err_device;', 1)
s = s.replace(
    '\tret = wg_genetlink_init();\n\tif (ret < 0)\n\t\tgoto err_netlink;',
    '\tret = wg_genetlink_init();\n\tpr_err("AWGDBG: genetlink_init=%d\\n", ret);\n\tif (ret < 0)\n\t\tgoto err_netlink;', 1)
s = s.replace(
    '\treturn 0;\n}\n\nstatic void __exit wg_mod_exit(void)',
    '\tpr_err("AWGDBG: init success\\n");\n\treturn 0;\n}\n\nstatic void __exit wg_mod_exit(void)', 1)
p.write_text(s)

p = Path('awg/src/netlink.c')
s = p.read_text()
needle = '#include <net/genetlink.h>\n'
probe = '''
static int awg_probe_doit(struct sk_buff *skb, struct genl_info *info)
{
\treturn 0;
}

static int awg_genl_probe_empty(void)
{
\tstatic struct genl_family probe = {
\t\t.name = "awgprobe0",
\t\t.version = 1,
\t\t.module = THIS_MODULE,
\t};
\tint ret = genl_register_family(&probe);
\tpr_err("AWGDBG: probe_empty register=%d ops=%px n_ops=%u mcgrps=%px n_mcgrps=%u\\n",
\t       ret, probe.ops, probe.n_ops, probe.mcgrps, probe.n_mcgrps);
\tif (!ret)
\t\tgenl_unregister_family(&probe);
\treturn ret;
}

static int awg_genl_probe_oneop(void)
{
\tstatic const struct genl_ops probe_ops[] = {
\t\t{ .cmd = 1, .doit = awg_probe_doit },
\t};
\tstatic struct genl_family probe = {
\t\t.name = "awgprobe1",
\t\t.version = 1,
\t\t.ops = probe_ops,
\t\t.n_ops = ARRAY_SIZE(probe_ops),
\t\t.module = THIS_MODULE,
\t};
\tint ret = genl_register_family(&probe);
\tpr_err("AWGDBG: probe_oneop register=%d family.ops=%px probe_ops=%px n_ops=%u cmd=%u doit=%px\\n",
\t       ret, probe.ops, probe_ops, probe.n_ops, probe_ops[0].cmd, probe_ops[0].doit);
\tif (!ret)
\t\tgenl_unregister_family(&probe);
\treturn ret;
}
'''
if probe not in s:
    s = s.replace(needle, needle + probe, 1)

old = '''int __init wg_genetlink_init(void)
{
\tpr_err("AWGDBG: MCGRPS_OFF_BUILD\\n");
\tpr_err("AWGDBG: genl sizeof_family=%zu sizeof_ops=%zu name=%s n_ops=%u n_mcgrps=%u\\n",
\t       sizeof(genl_family), sizeof(genl_ops), genl_family.name,
\t       genl_family.n_ops, genl_family.n_mcgrps);
\tpr_err("AWGDBG: genl op0 cmd=%u doit=%px dumpit=%px; op1 cmd=%u doit=%px dumpit=%px\\n",
\t       genl_ops[0].cmd, genl_ops[0].doit, genl_ops[0].dumpit,
\t       genl_ops[1].cmd, genl_ops[1].doit, genl_ops[1].dumpit);
\tpr_err("AWGDBG: genl mcgrp0 name=%s\\n", genl_family.n_mcgrps ? genl_family.mcgrps[0].name : "<none>");
\treturn genl_register_family(&genl_family);
}'''
new = '''int __init wg_genetlink_init(void)
{
\tpr_err("AWGDBG: PROBE_BEGIN\\n");
\tawg_genl_probe_empty();
\tawg_genl_probe_oneop();
\tpr_err("AWGDBG: MCGRPS_OFF_BUILD\\n");
\tpr_err("AWGDBG: genl sizeof_family=%zu sizeof_ops=%zu name=%s n_ops=%u n_mcgrps=%u\\n",
\t       sizeof(genl_family), sizeof(genl_ops), genl_family.name,
\t       genl_family.n_ops, genl_family.n_mcgrps);
\tpr_err("AWGDBG: family.ops=%px genl_ops=%px maxattr=%u policy=%px module=%px netnsok=%u parallel_ops=%u\\n",
\t       genl_family.ops, genl_ops, genl_family.maxattr, genl_family.policy,
\t       genl_family.module, genl_family.netnsok, genl_family.parallel_ops);
\tpr_err("AWGDBG: genl op0 cmd=%u doit=%px dumpit=%px; op1 cmd=%u doit=%px dumpit=%px\\n",
\t       genl_ops[0].cmd, genl_ops[0].doit, genl_ops[0].dumpit,
\t       genl_ops[1].cmd, genl_ops[1].doit, genl_ops[1].dumpit);
\tpr_err("AWGDBG: genl mcgrp0 name=%s\\n", genl_family.n_mcgrps ? genl_family.mcgrps[0].name : "<none>");
\treturn genl_register_family(&genl_family);
}'''
if old not in s:
    raise SystemExit('expected netlink init block not found')
s = s.replace(old, new, 1)
s = s.replace('.mcgrps = wg_genl_mcgrps,', '.mcgrps = NULL,', 1)
s = s.replace('.n_mcgrps = ARRAY_SIZE(wg_genl_mcgrps)', '.n_mcgrps = 0', 1)
p.write_text(s)
