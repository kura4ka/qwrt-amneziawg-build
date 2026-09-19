#!/bin/sh
set -eu
p="awg/src/device.c"
python3 - <<'PY'
from pathlib import Path
p=Path("awg/src/device.c")
s=p.read_text()
needle='static int wg_newlink(struct net_device *dev,\n\t\t\t      struct rtnl_newlink_params *params,\n\t\t\t      struct netlink_ext_ack *extack)\n{'
if needle not in s:
    raise SystemExit("wg_newlink anchor not found")
s=s.replace(needle, needle+'\n\tpr_err("AWGDBG: NEWLINK_ENTER dev=%px name=%s\\n", dev, dev ? dev->name : "<null>");',1)
repls=[
('rcu_assign_pointer(wg->creating_net, link_net);','pr_err("AWGDBG: NEWLINK_STEP creating_net\\n");\n\trcu_assign_pointer(wg->creating_net, link_net);'),
('wg_allowedips_init(&wg->peer_allowedips);','pr_err("AWGDBG: NEWLINK_STEP allowedips\\n");\n\twg_allowedips_init(&wg->peer_allowedips);'),
('wg->peer_hashtable = wg_pubkey_hashtable_alloc();','pr_err("AWGDBG: NEWLINK_STEP peer_hash_alloc\\n");\n\twg->peer_hashtable = wg_pubkey_hashtable_alloc();'),
('wg->index_hashtable = wg_index_hashtable_alloc();','pr_err("AWGDBG: NEWLINK_STEP index_hash_alloc\\n");\n\twg->index_hashtable = wg_index_hashtable_alloc();'),
('wg->handshake_receive_wq = alloc_workqueue("wg-kex-%s",','pr_err("AWGDBG: NEWLINK_STEP rx_wq\\n");\n\twg->handshake_receive_wq = alloc_workqueue("wg-kex-%s",'),
('wg->handshake_send_wq = alloc_workqueue("wg-kex-%s",','pr_err("AWGDBG: NEWLINK_STEP tx_wq\\n");\n\twg->handshake_send_wq = alloc_workqueue("wg-kex-%s",'),
('wg->packet_crypt_wq = alloc_workqueue("wg-crypt-%s",','pr_err("AWGDBG: NEWLINK_STEP crypt_wq\\n");\n\twg->packet_crypt_wq = alloc_workqueue("wg-crypt-%s",'),
('ret = wg_packet_queue_init(&wg->encrypt_queue, wg_packet_encrypt_worker,','pr_err("AWGDBG: NEWLINK_STEP encrypt_q\\n");\n\tret = wg_packet_queue_init(&wg->encrypt_queue, wg_packet_encrypt_worker,'),
('ret = wg_packet_queue_init(&wg->decrypt_queue, wg_packet_decrypt_worker,','pr_err("AWGDBG: NEWLINK_STEP decrypt_q\\n");\n\tret = wg_packet_queue_init(&wg->decrypt_queue, wg_packet_decrypt_worker,'),
('ret = wg_packet_queue_init(&wg->handshake_queue, wg_packet_handshake_receive_worker,','pr_err("AWGDBG: NEWLINK_STEP handshake_q\\n");\n\tret = wg_packet_queue_init(&wg->handshake_queue, wg_packet_handshake_receive_worker,'),
('ret = wg_ratelimiter_init();','pr_err("AWGDBG: NEWLINK_STEP ratelimiter\\n");\n\tret = wg_ratelimiter_init();'),
('netif_threaded_enable(dev);','pr_err("AWGDBG: NEWLINK_STEP threaded_enable\\n");\n\tnetif_threaded_enable(dev);'),
('ret = register_netdevice(dev);','pr_err("AWGDBG: NEWLINK_STEP register_netdevice\\n");\n\tret = register_netdevice(dev);\n\tpr_err("AWGDBG: NEWLINK_REGISTER_RET=%d\\n", ret);'),
('list_add(&wg->device_list, &device_list);','pr_err("AWGDBG: NEWLINK_STEP list_add\\n");\n\tlist_add(&wg->device_list, &device_list);'),
('\tpr_debug("%s: Interface created\\n", dev->name);','\tpr_err("AWGDBG: NEWLINK_SUCCESS name=%s\\n", dev->name);\n\tpr_debug("%s: Interface created\\n", dev->name);')
]
for a,b in repls:
    if a not in s: raise SystemExit("missing: "+a)
    s=s.replace(a,b,1)
p.write_text(s)
PY
