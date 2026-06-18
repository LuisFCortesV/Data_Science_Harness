"""Proyecto de ejemplo SIN git inicializado (valida la degradación de FR-006)."""

import pandas as pd

df = pd.read_csv("input.csv")
df.to_csv("output.csv")
