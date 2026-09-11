"""Part D Task 4: which of tRCD/tRP/tRAS/tCCD binds? Double each timing
one at a time (1-channel baseline) and measure avg read latency."""
import ramulator

def run(label, channels=1, **overrides):
    ddr4 = ramulator.dram.DDR4(org_preset="DDR4_8Gb_x8", timing_preset="DDR4_3200AA", rank=2, **overrides)
    ctrl = ramulator.controller.GenericDDR(
        dram=ddr4, scheduler=ramulator.scheduler.FRFCFS(),
        refresh_manager=ramulator.refresh_manager.AllBank(),
        row_policy=ramulator.row_policy.Open(),
        addr_mapper=ramulator.addr_mapper.RoBaRaCoCh())
    mem = ramulator.memory_system.GenericDRAM(clock_ratio=3, controllers=[ctrl]*channels,
                                              channel_mapper=ramulator.channel_mapper.CacheLineInterleave())
    sim = ramulator.Simulation(ramulator.frontend.LoadStoreTrace(clock_ratio=8, path="./l2miss_converted.trace"), mem)
    sim.run()
    s = sim.stats["memory_system"]["controller"]
    if isinstance(s, list): s = s[0]
    print(f"{label:16s} cycles={s['cycles']:7d}  avg_read_lat={s['avg_read_latency']:8.2f}")
    return s

run("baseline")
run("nRCD 22->44", nRCD=44)
run("nRP  22->44", nRP=44)
run("nRAS 52->104", nRAS=104)
run("nCCDS 4->8", nCCDS=8)
run("2-channel base", channels=2)
