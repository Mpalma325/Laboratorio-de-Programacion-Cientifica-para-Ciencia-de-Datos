"""
Custom Transformers for scikit-learn pipelines.
Feature engineering transformers for the predictive model.
"""

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class DatosHistoricos(BaseEstimator, TransformerMixin):
    """
    Transformer que agrega features históricos (shift) por cliente-producto.
    Crea columnas: items_prev, compra_prev
    """
    def __init__(self, c="customer_id", p="product_id",
                 week_col="week", items="items", n_orders="n_orders", compra="compra"):
        self.c, self.p, self.week_col = c, p, week_col
        self.items, self.n_orders, self.compra = items, n_orders, compra

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy().sort_values([self.c, self.p, self.week_col]).reset_index(drop=True)

        # Shift históricos
        df["items_prev"] = (
            df.groupby([self.c, self.p], sort=False)[self.items]
              .shift(1).fillna(0).astype("int16")
        )

        df["compra_prev"] = (
            df.groupby([self.c, self.p], sort=False)[self.compra]
              .shift(1).fillna(0).astype("int8")
        )

        return df

    def set_output(self, transform="default"):
        return self


class RecenciaSemanal(BaseEstimator, TransformerMixin):
    """
    Transformer que calcula la recencia (semanas desde última compra) del producto.
    Crea columna: recencia_producto
    """
    def __init__(self, c="customer_id", p="product_id",
                 week_col="week", compra="compra", inicio=1000):
        self.c, self.p, self.week_col, self.compra = c, p, week_col, compra
        self.inicio = inicio

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy().sort_values([self.c, self.p, self.week_col])

        wk = df[self.week_col]
        bought = df[self.compra].astype(bool)

        # Semana de la última compra del mismo producto
        last_prod = (
            wk.where(bought)  # semanas solo donde hubo compra
              .groupby([df[self.c], df[self.p]], sort=False)
              .ffill()  # última compra conocida
              .groupby([df[self.c], df[self.p]], sort=False)
              .shift(1)
        )

        # Recencia
        df["recencia_producto"] = (wk - last_prod).fillna(self.inicio).astype("int16")
        return df

    def set_output(self, transform="default"):
        return self


class PopularidadProductoPrev(BaseEstimator, TransformerMixin):
    """
    Transformer que calcula la popularidad previa del producto.
    Crea columna: popularity_prev
    """
    def __init__(self, p="product_id", week_col="week", compra="compra"):
        self.p, self.week_col, self.compra = p, week_col, compra

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy().sort_values([self.p, self.week_col])

        # compras por producto-semana
        n = (
            df.groupby([self.p, self.week_col], sort=False)[self.compra]
              .sum()
              .groupby(level=0, sort=False)
              .shift(1)
              .rename("popularity_prev")
              .reset_index()
        )

        df = df.merge(n, on=[self.p, self.week_col], how="left")
        df["popularity_prev"] = df["popularity_prev"].fillna(0).astype("float32")
        return df

    def set_output(self, transform="default"):
        return self


class CompraRelativa(BaseEstimator, TransformerMixin):
    """
    Transformer que calcula la frecuencia relativa de compra del producto.
    Crea columna: frec_producto
    """
    def __init__(self, c="customer_id", p="product_id", week_col="week", compra="compra"):
        self.c, self.p, self.week_col, self.compra = c, p, week_col, compra

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy().sort_values([self.c, self.p, self.week_col])
        g_cp = df.groupby([self.c, self.p], sort=False)

        compras_prev = g_cp[self.compra].cumsum().shift(1).fillna(0.0)
        n_prev = g_cp.cumcount()
        df["frec_producto"] = np.where(n_prev > 0, compras_prev / n_prev, 0.0).astype("float32")
        return df

    def set_output(self, transform="default"):
        return self