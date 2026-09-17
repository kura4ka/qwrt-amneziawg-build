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
