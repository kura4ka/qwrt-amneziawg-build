from pathlib import Path
import re

p = Path('awg/src/netlink.c')
s = p.read_text()

probe = r'''
static int awg_probe_doit(struct sk_buff *skb, struct genl_info *info)
{
	return 0;
}

static int awg_probe_start(struct netlink_callback *cb)
{
	return 0;
}

static int awg_probe_dumpit(struct sk_buff *skb, struct netlink_callback *cb)
{
	return 0;
}

static int awg_probe_done(struct netlink_callback *cb)
{
	return 0;
}

static void awg_probe_result(const char *tag, struct genl_family *family, int ret)
{
	pr_err("AWGDBG: %s=%d ops=%px n_ops=%u name=%s maxattr=%u policy=%px module=%px netnsok=%u parallel_ops=%u\n",
	       tag, ret, family->ops, family->n_ops, family->name,
	       family->maxattr, family->policy, family->module,
	       family->netnsok, family->parallel_ops);
	if (!ret)
		genl_unregister_family(family);
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

static void awg_genl_probe_matrix(void)
{
	static const struct genl_ops cmd0_ops[] = {
		{ .cmd = 0, .doit = awg_probe_doit },
	};
	static struct genl_family cmd0_family = {
		.name = "awgprobe2",
		.version = 1,
		.ops = cmd0_ops,
		.n_ops = ARRAY_SIZE(cmd0_ops),
		.module = THIS_MODULE,
	};
	static const struct genl_ops two_doit_ops[] = {
		{ .cmd = 0, .doit = awg_probe_doit },
		{ .cmd = 1, .doit = awg_probe_doit },
	};
	static struct genl_family two_doit_family = {
		.name = "awgprobe3",
		.version = 1,
		.ops = two_doit_ops,
		.n_ops = ARRAY_SIZE(two_doit_ops),
		.module = THIS_MODULE,
	};
	static const struct genl_ops two_flags_ops[] = {
		{ .cmd = 0, .doit = awg_probe_doit, .flags = GENL_UNS_ADMIN_PERM },
		{ .cmd = 1, .doit = awg_probe_doit, .flags = GENL_UNS_ADMIN_PERM },
	};
	static struct genl_family two_flags_family = {
		.name = "awgprobe4",
		.version = 1,
		.ops = two_flags_ops,
		.n_ops = ARRAY_SIZE(two_flags_ops),
		.module = THIS_MODULE,
	};
	static const struct genl_ops dump_ops[] = {
		{ .cmd = 0, .dumpit = awg_probe_dumpit },
	};
	static struct genl_family dump_family = {
		.name = "awgprobe5",
		.version = 1,
		.ops = dump_ops,
		.n_ops = ARRAY_SIZE(dump_ops),
		.module = THIS_MODULE,
	};
	static const struct genl_ops dump_full_ops[] = {
		{ .cmd = 0, .start = awg_probe_start, .dumpit = awg_probe_dumpit,
		  .done = awg_probe_done, .flags = GENL_UNS_ADMIN_PERM },
	};
	static struct genl_family dump_full_family = {
		.name = "awgprobe6",
		.version = 1,
		.ops = dump_full_ops,
		.n_ops = ARRAY_SIZE(dump_full_ops),
		.module = THIS_MODULE,
	};

	awg_probe_result("probe_cmd0", &cmd0_family,
			genl_register_family(&cmd0_family));
	awg_probe_result("probe_two_doit", &two_doit_family,
			genl_register_family(&two_doit_family));
	awg_probe_result("probe_two_flags", &two_flags_family,
			genl_register_family(&two_flags_family));
	awg_probe_result("probe_dump", &dump_family,
			genl_register_family(&dump_family));
	awg_probe_result("probe_dump_full", &dump_full_family,
			genl_register_family(&dump_full_family));
}
'''

if 'awg_genl_probe_matrix' not in s:
    anchor = 'static struct genl_family genl_family;\n'
    if anchor not in s:
        raise SystemExit('genl family anchor not found')
    s = s.replace(anchor, anchor + probe, 1)

s = s.replace('.mcgrps = wg_genl_mcgrps,', '.mcgrps = NULL,', 1)
s = s.replace('.n_mcgrps = ARRAY_SIZE(wg_genl_mcgrps)', '.n_mcgrps = 0', 1)

replacement = '''int __init wg_genetlink_init(void)
{
	pr_err("AWGDBG: PROBE_BEGIN\\n");
	awg_genl_probe_empty();
	awg_genl_probe_oneop();
	awg_genl_probe_matrix();
	pr_err("AWGDBG: MCGRPS_OFF_BUILD\\n");
	pr_err("AWGDBG: genl sizeof_family=%zu sizeof_ops=%zu name=%s n_ops=%u n_mcgrps=%u\\n",
	       sizeof(genl_family), sizeof(genl_ops), genl_family.name,
	       genl_family.n_ops, genl_family.n_mcgrps);
	pr_err("AWGDBG: family.ops=%px genl_ops=%px maxattr=%u policy=%px module=%px netnsok=%u parallel_ops=%u\\n",
	       genl_family.ops, genl_ops, genl_family.maxattr, genl_family.policy,
	       genl_family.module, genl_family.netnsok, genl_family.parallel_ops);
	pr_err("AWGDBG: genl op0 cmd=%u doit=%px dumpit=%px; op1 cmd=%u doit=%px dumpit=%px\\n",
	       genl_ops[0].cmd, genl_ops[0].doit, genl_ops[0].dumpit,
	       genl_ops[1].cmd, genl_ops[1].doit, genl_ops[1].dumpit);
	pr_err("AWGDBG: genl mcgrp0 name=%s\\n", genl_family.n_mcgrps ? genl_family.mcgrps[0].name : "<none>");
	return genl_register_family(&genl_family);
}'''

s, n = re.sub(
    r'int __init wg_genetlink_init\(void\)\n\{\n\s*return genl_register_family\(&genl_family\);\n\}',
    replacement,
    s,
    count=1,
)
if n != 1:
    raise SystemExit('generic netlink init anchor not found')

p.write_text(s)
