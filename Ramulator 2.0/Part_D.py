"""Part D — Ramulator 2.1 DDR4 sweep on the 2MB L2 miss stream."""
import ramulator

TRACE = ["./l2miss_converted.trace"]

def build(scheduler, addr_mapper, channels=1, label=""):
    frontend = ramulator.frontend.LoadStoreTrace(clock_ratio=8, path=TRACE[0])
    ddr4 = ramulator.dram.DDR4(org_preset="DDR4_8Gb_x8", timing_preset="DDR4_3200AA", rank=2)
    ctrl = ramulator.controller.GenericDDR(
        dram=ddr4,
        scheduler=scheduler,
        refresh_manager=ramulator.refresh_manager.AllBank(),
        row_policy=ramulator.row_policy.Open(),
        addr_mapper=addr_mapper,
    )
    mem = ramulator.memory_system.GenericDRAM(
        clock_ratio=3,
        controllers=[ctrl] * channels,
        channel_mapper=ramulator.channel_mapper.CacheLineInterleave(),
    )
    sim = ramulator.Simulation(frontend, mem)
    sim.run()
    s = sim.stats["memory_system"]["controller"]
    if isinstance(s, list):
        s = s[0]
    print(f"\n=== {label} ===")
    print(f"  cycles           = {s['cycles']}")
    print(f"  avg_read_latency = {s['avg_read_latency']:.2f} cycles")
    print(f"  row_hits         = {s['row_hits']}")
    print(f"  row_misses       = {s['row_misses']}")
    print(f"  row_conflicts    = {s['row_conflicts']}")
    hit_rate = s['row_hits'] / max(1, s['row_hits'] + s['row_misses'] + s['row_conflicts'])
    print(f"  row_buf_hit_rate = {hit_rate*100:.1f}%")
    return s

# Task 1 — baseline: FRFCFS, RoBaRaCoCh (row bits above bank/col)
t1 = build(ramulator.scheduler.FRFCFS(), ramulator.addr_mapper.RoBaRaCoCh(), 1, "Task1 baseline FRFCFS RoBaRaCoCh")

# Task 2 — FCFS proxy: use NoRefresh (no refresh overhead), buffer_size=1 forces in-order
ctrl_fcfs_like = ramulator.controller.GenericDDR(
    dram=ramulator.dram.DDR4(org_preset="DDR4_8Gb_x8", timing_preset="DDR4_3200AA", rank=2),
    scheduler=ramulator.scheduler.FRFCFS(),
    refresh_manager=ramulator.refresh_manager.NoRefresh(),
    row_policy=ramulator.row_policy.Open(),
    addr_mapper=ramulator.addr_mapper.RoBaRaCoCh(),
    read_buffer_size=1, write_buffer_size=1, priority_buffer_size=1,
)
mem2 = ramulator.memory_system.GenericDRAM(clock_ratio=3, controllers=[ctrl_fcfs_like],
                                            channel_mapper=ramulator.channel_mapper.CacheLineInterleave())
sim2 = ramulator.Simulation(ramulator.frontend.LoadStoreTrace(clock_ratio=8, path=TRACE[0]), mem2)
sim2.run()
s2 = sim2.stats["memory_system"]["controller"]
if isinstance(s2, list):
    s2 = s2[0]
print("\n=== Task2 FCFS-proxy (buffer=1, no reordering) ===")
print(f"  cycles = {s2['cycles']}  (vs baseline {t1['cycles']}, delta = {s2['cycles']-t1['cycles']} cycles, {(s2['cycles']/t1['cycles']-1)*100:+.1f}%)")
hit2 = s2['row_hits'] / max(1, s2['row_hits']+s2['row_misses']+s2['row_conflicts'])*100
hit1 = t1['row_hits'] / max(1, t1['row_hits']+t1['row_misses']+t1['row_conflicts'])*100
print(f"  row_buf_hit {hit1:.1f}% -> {hit2:.1f}%  avg_read_lat {t1['avg_read_latency']:.1f} -> {s2['avg_read_latency']:.1f} cyc")

# Task 3 — swap address mapping: row bits BELOW bank bits -> ChRaBaRoCo
t3 = build(ramulator.scheduler.FRFCFS(), ramulator.addr_mapper.ChRaBaRoCo(), 1, "Task3 ChRaBaRoCo (row<bank)")

# Task 4 — double channel count
t4 = build(ramulator.scheduler.FRFCFS(), ramulator.addr_mapper.RoBaRaCoCh(), 2, "Task4 2-channel")
print(f"\nTask4: cycles {t1['cycles']} -> {t4['cycles']} ({(1-t4['cycles']/t1['cycles'])*100:.1f}% improvement)")
