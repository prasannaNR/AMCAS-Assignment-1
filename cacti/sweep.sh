#!/bin/bash

echo "Capacity_KB  log2(Capacity_bytes)  Access_Time_ns"

for size in 262144 524288 1048576 2097152 4194304 8388608 16777216
do
    sed -i -E "s/^-size \(bytes\) [0-9]+/-size (bytes) $size/" cache.cfg

    access_time=$(./cacti -infile cache.cfg 2>/dev/null | \
        grep "Access time (ns):" | head -1 | \
        awk '{print $4}')

    log2=$(python3 -c "import math; print(math.log2($size))")

    kb=$((size / 1024))

    echo "$kb        $log2        $access_time"
done

cp cache_original.cfg cache.cfg
