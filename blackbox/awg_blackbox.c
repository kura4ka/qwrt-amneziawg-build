#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/spinlock.h>
#include <linux/timekeeping.h>
#include <linux/sched.h>
#include <linux/notifier.h>
#include <linux/netdevice.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/kmsg_dump.h>
#include <linux/printk.h>
#include <linux/vmalloc.h>

#define AWG_BB_ENTRIES 1024
#define AWG_BB_MSG 192

struct awg_bb_entry {
    u64 ns;
    u32 cpu;
    u32 pid;
    char comm[TASK_COMM_LEN];
    char msg[AWG_BB_MSG];
};

static struct awg_bb_entry *ring;
static unsigned int head;
static spinlock_t ring_lock;
static struct proc_dir_entry *proc_ent;

static void __awg_bb_event(const char *fmt, va_list ap)
{
    unsigned long flags;
    struct awg_bb_entry *e;
    unsigned int idx;

    if (!ring)
        return;

    spin_lock_irqsave(&ring_lock, flags);
    idx = head++ & (AWG_BB_ENTRIES - 1);
    e = &ring[idx];
    e->ns = ktime_get_ns();
    e->cpu = raw_smp_processor_id();
    e->pid = current->pid;
    get_task_comm(e->comm, current);
    vscnprintf(e->msg, sizeof(e->msg), fmt, ap);
    spin_unlock_irqrestore(&ring_lock, flags);
}

void awg_bb_event(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    __awg_bb_event(fmt, ap);
    va_end(ap);
}
EXPORT_SYMBOL_GPL(awg_bb_event);

static int awg_bb_seq_show(struct seq_file *m, void *v)
{
    unsigned long flags;
    unsigned int i, n, start;

    spin_lock_irqsave(&ring_lock, flags);
    n = head < AWG_BB_ENTRIES ? head : AWG_BB_ENTRIES;
    start = head < AWG_BB_ENTRIES ? 0 : head & (AWG_BB_ENTRIES - 1);
    for (i = 0; i < n; ++i) {
        struct awg_bb_entry *e = &ring[(start + i) & (AWG_BB_ENTRIES - 1)];
        seq_printf(m, "%llu cpu=%u pid=%u comm=%s %s\n",
                   e->ns, e->cpu, e->pid, e->comm, e->msg);
    }
    spin_unlock_irqrestore(&ring_lock, flags);
    return 0;
}

static int awg_bb_open(struct inode *inode, struct file *file)
{
    return single_open(file, awg_bb_seq_show, NULL);
}

static const struct file_operations awg_bb_fops = {
    .owner = THIS_MODULE,
    .open = awg_bb_open,
    .read = seq_read,
    .llseek = seq_lseek,
    .release = single_release,
};

static const char * const netdev_events[] = {
    [NETDEV_UP] = "NETDEV_UP",
    [NETDEV_DOWN] = "NETDEV_DOWN",
    [NETDEV_REBOOT] = "NETDEV_REBOOT",
    [NETDEV_CHANGE] = "NETDEV_CHANGE",
    [NETDEV_REGISTER] = "NETDEV_REGISTER",
    [NETDEV_UNREGISTER] = "NETDEV_UNREGISTER",
    [NETDEV_CHANGEMTU] = "NETDEV_CHANGEMTU",
    [NETDEV_CHANGEADDR] = "NETDEV_CHANGEADDR",
    [NETDEV_PRE_CHANGEADDR] = "NETDEV_PRE_CHANGEADDR",
    [NETDEV_GOING_DOWN] = "NETDEV_GOING_DOWN",
    [NETDEV_CHANGEINFODATA] = "NETDEV_CHANGEINFODATA",
    [NETDEV_PRE_UP] = "NETDEV_PRE_UP",
};

static int awg_bb_netdev(struct notifier_block *nb, unsigned long event, void *ptr)
{
    struct net_device *dev = netdev_notifier_info_to_dev(ptr);
    const char *name = event < ARRAY_SIZE(netdev_events) && netdev_events[event] ?
                       netdev_events[event] : "NETDEV_OTHER";

    if (dev)
        awg_bb_event("NETDEV %s dev=%s ifindex=%d flags=0x%x oper=%u",
                     name, dev->name, dev->ifindex, dev->flags, dev->operstate);
    return NOTIFY_DONE;
}

static struct notifier_block netdev_nb = {
    .notifier_call = awg_bb_netdev,
};

static int awg_bb_die(struct notifier_block *nb, unsigned long val, void *data)
{
    struct die_args *args = data;

    if (args)
        pr_emerg("AWGBB: DIE val=%lu err=%d trap=%d pc=%px\n", val,
                 args->err, args->trapnr,
                 args->regs ? (void *)instruction_pointer(args->regs) : NULL);
    else
        pr_emerg("AWGBB: DIE val=%lu\n", val);

    awg_bb_event("DIE val=%lu", val);
    return NOTIFY_DONE;
}

static struct notifier_block die_nb = {
    .notifier_call = awg_bb_die,
    .priority = 200,
};

static int awg_bb_panic(struct notifier_block *nb, unsigned long val, void *data)
{
    pr_emerg("AWGBB: PANIC notifier val=%lu msg=%s\n", val,
             data ? (char *)data : "<none>");
    awg_bb_event("PANIC val=%lu msg=%s", val,
                 data ? (char *)data : "<none>");
    return NOTIFY_DONE;
}

static struct notifier_block panic_nb = {
    .notifier_call = awg_bb_panic,
    .priority = 200,
};

static void awg_bb_kmsg_dump(struct kmsg_dumper *dumper,
                             enum kmsg_dump_reason reason)
{
    char buf[512];
    size_t len = 0;

    if (kmsg_dump_get_buffer(dumper, false, buf, sizeof(buf) - 1, &len) && len) {
        buf[len] = '\0';
        pr_emerg("AWGBB: KMSG reason=%d tail=%s\n", reason, buf);
    }
}

static struct kmsg_dumper kmsg_dumper = {
    .dump = awg_bb_kmsg_dump,
};

static int __init awg_bb_init(void)
{
    int ret;

    ring = vzalloc(sizeof(*ring) * AWG_BB_ENTRIES);
    if (!ring)
        return -ENOMEM;

    spin_lock_init(&ring_lock);

    proc_ent = proc_create("awg_blackbox", 0444, NULL, &awg_bb_fops);
    if (!proc_ent) {
        vfree(ring);
        ring = NULL;
        return -ENOMEM;
    }

    ret = register_netdevice_notifier(&netdev_nb);
    if (ret)
        goto err_proc;

    ret = register_die_notifier(&die_nb);
    if (ret)
        goto err_netdev;

    ret = register_panic_notifier(&panic_nb);
    if (ret)
        goto err_die;

    ret = kmsg_dump_register(&kmsg_dumper);
    if (ret)
        goto err_panic;

    awg_bb_event("BLACKBOX_INIT entries=%u", AWG_BB_ENTRIES);
    pr_info("AWGBB: loaded; /proc/awg_blackbox\n");
    return 0;

err_panic:
    unregister_panic_notifier(&panic_nb);
err_die:
    unregister_die_notifier(&die_nb);
err_netdev:
    unregister_netdevice_notifier(&netdev_nb);
err_proc:
    proc_remove(proc_ent);
    vfree(ring);
    ring = NULL;
    return ret;
}

static void __exit awg_bb_exit(void)
{
    kmsg_dump_unregister(&kmsg_dumper);
    unregister_panic_notifier(&panic_nb);
    unregister_die_notifier(&die_nb);
    unregister_netdevice_notifier(&netdev_nb);
    proc_remove(proc_ent);
    vfree(ring);
    ring = NULL;
    pr_info("AWGBB: unloaded\n");
}

module_init(awg_bb_init);
module_exit(awg_bb_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("QWRT AWG diagnostics");
MODULE_DESCRIPTION("AmneziaWG kernel blackbox crash/event logger");
