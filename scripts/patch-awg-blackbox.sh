#!/bin/sh
set -eu
python3 - <<'PY'
from pathlib import Path
p = Path("awg/src/device.c")
s = p.read_text()
inc = '#include "awg_blackbox.h"\n'
if inc not in s:
    s = inc + s

repls = [
("struct wg_device *wg = netdev_priv(dev);\n\tint ret = -ENOMEM, i;",
 "struct wg_device *wg = netdev_priv(dev);\n\tint ret = -ENOMEM, i;\n\tawg_bb_event(\"NEWLINK_ENTER dev=%px name=%s\", dev, dev ? dev->name : \"<null>\");"),
("\trcu_assign_pointer(wg->creating_net, link_net);",
 "\tawg_bb_event(\"NEWLINK_AFTER_NET_RESOLVE\");\n\trcu_assign_pointer(wg->creating_net, link_net);"),
("\twg->peer_hashtable = wg_pubkey_hashtable_alloc();",
 "\tawg_bb_event(\"HASH_PEER_BEGIN\");\n\twg->peer_hashtable = wg_pubkey_hashtable_alloc();"),
("\tif (!wg->peer_hashtable)\n\t\treturn ret;",
 "\tif (!wg->peer_hashtable)\n\t\treturn ret;\n\tawg_bb_event(\"HASH_PEER_OK\");"),
("\twg->index_hashtable = wg_index_hashtable_alloc();",
 "\tawg_bb_event(\"HASH_INDEX_BEGIN\");\n\twg->index_hashtable = wg_index_hashtable_alloc();"),
("\tif (!wg->index_hashtable)\n\t\tgoto err_free_peer_hashtable;",
 "\tif (!wg->index_hashtable)\n\t\tgoto err_free_peer_hashtable;\n\tawg_bb_event(\"HASH_INDEX_OK\");"),
("\twg->handshake_receive_wq = alloc_workqueue(\"wg-kex-%s\",",
 "\tawg_bb_event(\"WORKQUEUE_RX_BEGIN\");\n\twg->handshake_receive_wq = alloc_workqueue(\"wg-kex-%s\","),
("\tif (!wg->handshake_receive_wq)\n\t\tgoto err_free_tstats;",
 "\tif (!wg->handshake_receive_wq)\n\t\tgoto err_free_tstats;\n\tawg_bb_event(\"WORKQUEUE_RX_OK\");"),
("\twg->handshake_send_wq = alloc_workqueue(\"wg-kex-%s\",",
 "\tawg_bb_event(\"WORKQUEUE_TX_BEGIN\");\n\twg->handshake_send_wq = alloc_workqueue(\"wg-kex-%s\","),
("\tif (!wg->handshake_send_wq)\n\t\tgoto err_destroy_handshake_receive;",
 "\tif (!wg->handshake_send_wq)\n\t\tgoto err_destroy_handshake_receive;\n\tawg_bb_event(\"WORKQUEUE_TX_OK\");"),
("\twg->packet_crypt_wq = alloc_workqueue(\"wg-crypt-%s\",",
 "\tawg_bb_event(\"WORKQUEUE_CRYPT_BEGIN\");\n\twg->packet_crypt_wq = alloc_workqueue(\"wg-crypt-%s\","),
("\tif (!wg->packet_crypt_wq)\n\t\tgoto err_destroy_handshake_send;",
 "\tif (!wg->packet_crypt_wq)\n\t\tgoto err_destroy_handshake_send;\n\tawg_bb_event(\"WORKQUEUE_CRYPT_OK\");"),
("\tret = wg_packet_queue_init(&wg->encrypt_queue, wg_packet_encrypt_worker,",
 "\tawg_bb_event(\"QUEUE_ENCRYPT_BEGIN\");\n\tret = wg_packet_queue_init(&wg->encrypt_queue, wg_packet_encrypt_worker,"),
("\tret = wg_packet_queue_init(&wg->decrypt_queue, wg_packet_decrypt_worker,",
 "\tawg_bb_event(\"QUEUE_DECRYPT_BEGIN\");\n\tret = wg_packet_queue_init(&wg->decrypt_queue, wg_packet_decrypt_worker,"),
("\tret = wg_packet_queue_init(&wg->handshake_queue, wg_packet_handshake_receive_worker,",
 "\tawg_bb_event(\"QUEUE_HANDSHAKE_BEGIN\");\n\tret = wg_packet_queue_init(&wg->handshake_queue, wg_packet_handshake_receive_worker,"),
("\tret = wg_ratelimiter_init();",
 "\tawg_bb_event(\"RATELIMITER_BEGIN\");\n\tret = wg_ratelimiter_init();"),
("\tnetif_threaded_enable(dev);\n\tret = register_netdevice(dev);",
 "\tawg_bb_event(\"NETIF_THREADED_ENABLE_BEGIN\");\n\tnetif_threaded_enable(dev);\n\tawg_bb_event(\"NETIF_THREADED_ENABLE_DONE\");\n\tawg_bb_event(\"REGISTER_NETDEVICE_BEGIN\");\n\tret = register_netdevice(dev);"),
("\tret = register_netdevice(dev);\n\tif (ret < 0)",
 "\tret = register_netdevice(dev);\n\tawg_bb_event(\"REGISTER_NETDEVICE_RETURN ret=%d\", ret);\n\tif (ret < 0)"),
("\tdev->priv_destructor = wg_destruct;",
 "\tawg_bb_event(\"DEVICE_LIST_ADD_DONE\");\n\tdev->priv_destructor = wg_destruct;"),
("\tpr_debug(\"%s: Interface created\\n\", dev->name);",
 "\tawg_bb_event(\"NEWLINK_DONE name=%s\", dev->name);\n\tpr_debug(\"%s: Interface created\\n\", dev->name);")
]
for old,new in repls:
    if old not in s:
        raise SystemExit("missing anchor: "+old[:100])
    s=s.replace(old,new,1)
p.write_text(s)
PY
