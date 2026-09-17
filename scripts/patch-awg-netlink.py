from pathlib import Path

p = Path('awg/src/netlink.c')
s = p.read_text()

probe = r'''
static int awg_probe_doit(struct sk_buff *skb, struct genl_info *info)
{
	return 0;
}

static int awg_genl_probe_empty(void)
{
	static struct genl_family probe = {
		.name = "awgprobe0",
		.version = 1,
		.module = THIS_MODULE,
	};
	int ret = genl_register_family(&probe);
	pr_err("AWGDBG: probe_empty register=%d ops=%px n_ops=%u mcgrps=%px n_mcgrps=%u\n",
	       ret, probe.ops, probe.n_ops, probe.mcgrps, probe.n_mcgrps);
	if (!ret)
		genl_unregister_family(&probe);
	return ret;
}

static int awg_genl_probe_oneop(void)
{
	static const struct genl_ops probe_ops[] = {
		{ .cmd = 1, .doit = awg_probe_doit },
	};
	static struct genl_family probe = {
		.name = "awgprobe1",
		.version = 1,
		.ops = probe_ops,
		.n_ops = ARRAY_SIZE(probe_ops),
		.module = THIS_MODULE,
	};
	int ret = genl_register_family(&probe);
	pr_err("AWGDBG: probe_oneop register=%d family.ops=%px probe_ops=%px n_ops=%u cmd=%u doit=%px\n",
	       ret, probe.ops, probe_ops, probe.n_ops, probe_ops[0].cmd, probe_ops[0].doit);
	if (!ret)
		genl_unregister_family(&probe);
	return ret;
}
'''

anchor = 'int __init wg_genetlink_init(void)\n{\n\treturn genl_register_family(&genl_family);\n}'
replacement = r'''int __init wg_genetlink_init(void)
{
	pr_err("AWGDBG: PROBE_BEGIN\n");
	awg_genl_probe_empty();
	awg_genl_probe_oneop();
	pr_err("AWGDBG: MCGRPS_OFF_BUILD\n");
	pr_err("AWGDBG: genl sizeof_family=%zu sizeof_ops=%zu name=%s n_ops=%u n_mcgrps=%u\n",
	       sizeof(genl_family), sizeof(genl_ops), genl_family.name,
	       genl_family.n_ops, genl_family.n_mcgrps);
	pr_err("AWGDBG: family.ops=%px genl_ops=%px maxattr=%u policy=%px module=%px netnsok=%u parallel_ops=%u\n",
	       genl_family.ops, genl_ops, genl_family.maxattr, genl_family.policy,
	       genl_family.module, genl_family.netnsok, genl_family.parallel_ops);
	pr_err("AWGDBG: genl op0 cmd=%u doit=%px dumpit=%px; op1 cmd=%u doit=%px dumpit=%px\n",
	       genl_ops[0].cmd, genl_ops[0].doit, genl_ops[0].dumpit,
	       genl_ops[1].cmd, genl_ops[1].doit, genl_ops[1].dumpit);
	pr_err("AWGDBG: genl mcgrp0 name=%s\n", genl_family.n_mcgrps ? genl_family.mcgrps[0].name : "<none>");
	return genl_register_family(&genl_family);
}'''

if 'awg_genl_probe_empty' not in s:
    s = s.replace('static struct genl_family genl_family;\n', 'static struct genl_family genl_family;\n' + probe, 1)
if anchor not in s:
    raise SystemExit('generic netlink init anchor not found')
s = s.replace(anchor, replacement, 1)
if '.mcgrps = wg_genl_mcgrps,' in s:
    s = s.replace('.mcgrps = wg_genl_mcgrps,', '.mcgrps = NULL,', 1)
if '.n_mcgrps = ARRAY_SIZE(wg_genl_mcgrps)' in s:
    s = s.replace('.n_mcgrps = ARRAY_SIZE(wg_genl_mcgrps)', '.n_mcgrps = 0', 1)
p.write_text(s)
