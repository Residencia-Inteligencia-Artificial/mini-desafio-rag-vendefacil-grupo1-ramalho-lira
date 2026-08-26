from __future__ import annotations
import os
import pandas as pd


class StructuredStore:
    def __init__(self, data_dir: str):
        self.customers = pd.read_csv(os.path.join(data_dir, "structured", "customers.csv"))
        self.sales = pd.read_csv(os.path.join(data_dir, "structured", "sales.csv"))
        self.system_logs = pd.read_csv(os.path.join(data_dir, "semi_structured", "system_logs.csv"))

    def cliente_por_id(self, customer_id: str) -> dict | None:
        linha = self.customers[self.customers["customer_id"] == customer_id]
        return linha.iloc[0].to_dict() if not linha.empty else None

    def vendas_por_cliente(self, customer_id: str) -> pd.DataFrame:
        return self.sales[self.sales["customer_id"] == customer_id]

    def vendas_por_estado(self, state: str) -> pd.DataFrame:
        return self.sales[self.sales["state"] == state]

    def total_vendas_por_estado(self) -> pd.Series:
        return self.sales.groupby("state")["amount_brl"].sum().sort_values(ascending=False)

    def logs_por_customer_e_codigo_erro(self, customer_id: str, error_code: str | None = None) -> pd.DataFrame:
        df = self.system_logs[self.system_logs["customer_id"] == customer_id]
        if error_code:
            df = df[df["error_code"] == error_code]
        return df

    def resumo(self) -> dict:
        return {
            "clientes": len(self.customers),
            "vendas": len(self.sales),
            "logs": len(self.system_logs),
        }
