from pathlib import Path
import re

p = Path('awg/src/netlink.c')
s = p.read_text()

# QSDK compatibility: some vendor Generic Netlink validators expect the
# attribute policy on each operation rather than only on genl_family.
s = re.sub(r'(\\.cmd = WG_CMD_GET_DEVICE,\\n)', r'\\1\\t\\t.policy = device_policy,\\n', s, count=1)
s = re.sub(r'(\\.cmd = WG_CMD_SET_DEVICE,\\n)', r'\\1\\t\\t.policy = device_policy,\\n', s, count=1)

probe = r'''
static int awg_probe_doit(struct sk_buff *skb, struct genl_info *info)
{
\treturn 0;
}

static int awg_probe_start(struct netlink_callback *cb)
{
\treturn 0;
}

static int awg_probe_dumpit(struct sk_buff *skb, struct netlink_callback *cb)
{
\treturn 0;
}

static int awg_probe_done(struct netlink_callback *cb)
{
\treturn 0;
}

static void awg_probe_result(const char *tag, struct genl_family *family, int ret)
{
\tpr_err("AWGDBG: %s=%d ops=%px n_ops=%u name=%s maxattr=%u policy=%px module=%px netnsok=%u parallel_ops=%u\\n",
\t       tag, ret, family->ops, family->n_ops, family->name,
\t       family->maxattr, family->policy, family->module,
\t       family->netnsok, family->parallel_ops);
\tif (!ret)
\t\tgenl_unregister_family(family);
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

static void awg_genl_probe_register_ops(void)
{
	static struct genl_ops ops[] = {
		{ .cmd = 1, .doit = awg_probe_doit },
		{ .cmd = 2, .doit = awg_probe_doit },
	};
	static struct genl_family family = {
		.name = "awgprobe11",
		.version = 1,
		.module = THIS_MODULE,
	};
	int ret;

	ret = genl_register_family_with_ops(&family, ops, ARRAY_SIZE(ops));
	pr_err("AWGDBG: probe_family_with_ops=%d n_ops=%u ops=%px\\n",
	       ret, family.n_ops, family.ops);
	if (!ret)
		genl_unregister_family(&family);
}
static void awg_genl_probe_extra(void)
{
	static const struct genl_ops pair12_ops[] = {
		{ .cmd = 1, .doit = awg_probe_doit },
		{ .cmd = 2, .doit = awg_probe_doit },
	};
	static struct genl_family pair12_family = {
		.name = "awgprobe7",
		.version = 1,
		.ops = pair12_ops,
		.n_ops = ARRAY_SIZE(pair12_ops),
		.module = THIS_MODULE,
	};
	static const struct genl_ops pair13_ops[] = {
		{ .cmd = 1, .doit = awg_probe_doit },
		{ .cmd = 3, .doit = awg_probe_doit },
	};
	static struct genl_family pair13_family = {
		.name = "awgprobe8",
		.version = 1,
		.ops = pair13_ops,
		.n_ops = ARRAY_SIZE(pair13_ops),
		.module = THIS_MODULE,
	};
	static const struct genl_ops duplicate_ops[] = {
		{ .cmd = 1, .doit = awg_probe_doit },
		{ .cmd = 1, .doit = awg_probe_doit },
	};
	static struct genl_family duplicate_family = {
		.name = "awgprobe9",
		.version = 1,
		.ops = duplicate_ops,
		.n_ops = ARRAY_SIZE(duplicate_ops),
		.module = THIS_MODULE,
	};
	static struct genl_family second_only_family = {
		.name = "awgprobe10",
		.version = 1,
		.ops = pair12_ops + 1,
		.n_ops = 1,
		.module = THIS_MODULE,
	};

	pr_err("AWGDBG: sizeof family=%zu ops=%zu; offsets family.ops=%zu n_ops=%zu maxattr=%zu module=%zu netnsok=%zu; ops.cmd=%zu doit=%zu dumpit=%zu flags=%zu\n",
	       sizeof(struct genl_family), sizeof(struct genl_ops),
	       offsetof(struct genl_family, ops), offsetof(struct genl_family, n_ops),
	       offsetof(struct genl_family, maxattr), offsetof(struct genl_family, module),
	       offsetof(struct genl_family, netnsok), offsetof(struct genl_ops, cmd),
	       offsetof(struct genl_ops, doit), offsetof(struct genl_ops, dumpit),
	       offsetof(struct genl_ops, flags));
	pr_err("AWGDBG: pair12 ptr=%px size=%zu op0(cmd=%u doit=%px) op1(cmd=%u doit=%px)\n",
	       pair12_ops, sizeof(pair12_ops), pair12_ops[0].cmd, pair12_ops[0].doit,
	       pair12_ops[1].cmd, pair12_ops[1].doit);

	awg_probe_result("probe_pair12", &pair12_family,
			genl_register_family(&pair12_family));
	awg_probe_result("probe_pair13", &pair13_family,
			genl_register_family(&pair13_family));
	awg_probe_result("probe_duplicate", &duplicate_family,
			genl_register_family(&duplicate_family));
	awg_probe_result("probe_second_only", &second_only_family,
			genl_register_family(&second_only_family));
}

static void awg_genl_probe_matrix(void)
{
\tstatic const struct genl_ops cmd0_ops[] = {
\t\t{ .cmd = 0, .doit = awg_probe_doit },
\t};
\tstatic struct genl_family cmd0_family = {
\t\t.name = "awgprobe2",
\t\t.version = 1,
\t\t.ops = cmd0_ops,
\t\t.n_ops = ARRAY_SIZE(cmd0_ops),
\t\t.module = THIS_MODULE,
\t};
\tstatic const struct genl_ops two_doit_ops[] = {
\t\t{ .cmd = 0, .doit = awg_probe_doit },
\t\t{ .cmd = 1, .doit = awg_probe_doit },
\t};
\tstatic struct genl_family two_doit_family = {
\t\t.name = "awgprobe3",
\t\t.version = 1,
\t\t.ops = two_doit_ops,
\t\t.n_ops = ARRAY_SIZE(two_doit_ops),
\t\t.module = THIS_MODULE,
\t};
\tstatic const struct genl_ops two_flags_ops[] = {
\t\t{ .cmd = 0, .doit = awg_probe_doit, .flags = GENL_UNS_ADMIN_PERM },
\t\t{ .cmd = 1, .doit = awg_probe_doit, .flags = GENL_UNS_ADMIN_PERM },
\t};
\tstatic struct genl_family two_flags_family = {
\t\t.name = "awgprobe4",
\t\t.version = 1,
\t\t.ops = two_flags_ops,
\t\t.n_ops = ARRAY_SIZE(two_flags_ops),
\t\t.module = THIS_MODULE,
\t};
\tstatic const struct genl_ops dump_ops[] = {
\t\t{ .cmd = 0, .dumpit = awg_probe_dumpit },
\t};
\tstatic struct genl_family dump_family = {
\t\t.name = "awgprobe5",
\t\t.version = 1,
\t\t.ops = dump_ops,
\t\t.n_ops = ARRAY_SIZE(dump_ops),
\t\t.module = THIS_MODULE,
\t};
\tstatic const struct genl_ops dump_full_ops[] = {
\t\t{ .cmd = 0, .start = awg_probe_start, .dumpit = awg_probe_dumpit,
\t\t  .done = awg_probe_done, .flags = GENL_UNS_ADMIN_PERM },
\t};
\tstatic struct genl_family dump_full_family = {
\t\t.name = "awgprobe6",
\t\t.version = 1,
\t\t.ops = dump_full_ops,
\t\t.n_ops = ARRAY_SIZE(dump_full_ops),
\t\t.module = THIS_MODULE,
\t};

\tawg_probe_result("probe_cmd0", &cmd0_family,
\t\t\tgenl_register_family(&cmd0_family));
\tawg_probe_result("probe_two_doit", &two_doit_family,
\t\t\tgenl_register_family(&two_doit_family));
\tawg_probe_result("probe_two_flags", &two_flags_family,
\t\t\tgenl_register_family(&two_flags_family));
\tawg_probe_result("probe_dump", &dump_family,
\t\t\tgenl_register_family(&dump_family));
\tawg_probe_result("probe_dump_full", &dump_full_family,
\t\t\tgenl_register_family(&dump_full_family));
}
'''

if 'awg_genl_probe_matrix' not in s:
    anchor = 'static struct genl_family genl_family;\n'
    if anchor not in s:
        raise SystemExit('genl family anchor not found')
    probe = probe.replace('\\t', '\t')
    s = s.replace(anchor, anchor + probe, 1)

s = s.replace('.mcgrps = wg_genl_mcgrps,', '.mcgrps = NULL,', 1)
s = s.replace('.n_mcgrps = ARRAY_SIZE(wg_genl_mcgrps)', '.n_mcgrps = 0', 1)

replacement = '''int __init wg_genetlink_init(void)
{
\tpr_err("AWGDBG: PROBE_BEGIN\\n");
\tawg_genl_probe_empty();
\tawg_genl_probe_oneop();
\tawg_genl_probe_matrix();
\tawg_genl_probe_extra();\n\tawg_genl_probe_register_ops();
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

s = re.sub(
    r'int __init wg_genetlink_init\(void\)\n\{\n\s*return genl_register_family\(&genl_family\);\n\}',
    lambda _m: replacement,
    s,
    count=1,
)

if 'AWGDBG: PROBE_BEGIN' not in s:
    raise SystemExit('generic netlink init anchor not found')

p.write_text(s)
