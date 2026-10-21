"""Read the treatment file (plot, inoculation timing, variety, replication) into out/treatment.pkl."""
import sys, pandas as pd
t = pd.read_excel(sys.argv[1])
t.columns = ["Plot", "Inoculation", "Variety_t", "Replication"]
t = t.set_index("Plot")
t["Replication"] = t.Replication.replace({"Control/healthy": "C"})
t.to_pickle(sys.argv[2])
print(t.Replication.value_counts().to_dict())
