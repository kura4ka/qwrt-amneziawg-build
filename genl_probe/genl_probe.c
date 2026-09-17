// SPDX-License-Identifier: GPL-2.0
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/types.h>

/* QSDK 12.5 genl_family layout through n_ops/n_mcgrps. */
struct qws_genl_family_view {
	int id;
	unsigned int hdrsize;
	char name[16];
	unsigned int version;
	unsigned int maxattr;
	bool netnsok;
	bool parallel_ops;
	const void *policy;
	void *pre_doit;
	void *post_doit;
	void *attrbuf;
	const void *ops;
	const void *mcgrps;
	unsigned int n_ops;
	unsigned int n_mcgrps;
	unsigned int mcgrp_offset;
	void *module;
};

struct qws_genl_ops_view {
	void *doit;
	void *start;
	void *dumpit;
	void *done;
	u8 cmd;
	u8 internal_flags;
	u8 flags;
	u8 validate;
};

static int genl_probe_pre(struct kprobe *p, struct pt_regs *regs)
{
	struct qws_genl_family_view *f =
		(struct qws_genl_family_view *)regs->regs[0];
	const struct qws_genl_ops_view *ops;
	unsigned int i, n;

	if (!f)
		return 0;

	n = f->n_ops;
	if (n > 8)
		n = 8;

	pr_info("GENLPROBE enter name=%s n_ops=%u n_mcgrps=%u maxattr=%u netnsok=%u parallel_ops=%u family=%px ops=%px module=%px\n",
		f->name, f->n_ops, f->n_mcgrps, f->maxattr,
		f->netnsok, f->parallel_ops, f, f->ops, f->module);

	ops = (const struct qws_genl_ops_view *)f->ops;
	for (i = 0; i < n; ++i) {
		const struct qws_genl_ops_view *op = &ops[i];
		pr_info("GENLPROBE op%u cmd=%u doit=%px dumpit=%px start=%px done=%px flags=0x%x validate=0x%x\n",
			i, op->cmd, op->doit, op->dumpit, op->start, op->done,
			op->flags, op->validate);
	}

	return 0;
}

static int genl_probe_ret(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	long ret = regs_return_value(regs);
	pr_info("GENLPROBE return=%ld\n", ret);
	return 0;
}

static struct kretprobe genl_probe = {
	.kp = {
		.symbol_name = "genl_register_family",
		.pre_handler = genl_probe_pre,
	},
	.handler = genl_probe_ret,
	.maxactive = 32,
};

static int __init genl_probe_init(void)
{
	int ret = register_kretprobe(&genl_probe);
	if (ret) {
		pr_err("GENLPROBE register_kretprobe failed=%d\n", ret);
		return ret;
	}
	pr_info("GENLPROBE loaded\n");
	return 0;
}

static void __exit genl_probe_exit(void)
{
	unregister_kretprobe(&genl_probe);
	pr_info("GENLPROBE unloaded\n");
}

module_init(genl_probe_init);
module_exit(genl_probe_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("QWRT generic-netlink register_family kprobe");
