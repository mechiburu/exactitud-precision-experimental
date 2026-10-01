from __future__ import annotations
import math
import numpy as np
from scipy import stats

def compute_statistics(values, reference):
    x = np.asarray(values, dtype=float)
    if x.size < 2:
        raise ValueError("Se necesitan al menos 2 valores válidos.")

    n = int(x.size)
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    median = float(np.median(x))
    minimum = float(np.min(x))
    maximum = float(np.max(x))
    data_range = float(maximum - minimum)
    absolute_difference = abs(mean - float(reference))
    rmse = float(np.sqrt(np.mean((x - float(reference)) ** 2)))

    sem = std / math.sqrt(n)
    tcrit = float(stats.t.ppf(0.975, df=n - 1))
    ci_low = mean - tcrit * sem
    ci_high = mean + tcrit * sem

    if float(reference) != 0.0:
        error_relative_pct = 100.0 * absolute_difference / abs(float(reference))
        dispersion_relative_pct = 100.0 * std / abs(float(reference))
        rmse_relative_pct = 100.0 * rmse / abs(float(reference))
    else:
        error_relative_pct = None
        dispersion_relative_pct = None
        rmse_relative_pct = None

    return {
        "N": n,
        "Promedio": mean,
        "Desviación estándar": std,
        "Diferencia con referencia": absolute_difference,
        "Error relativo (%)": error_relative_pct,
        "Dispersión relativa (%)": dispersion_relative_pct,
        "RMSE": rmse,
        "RMSE relativo (%)": rmse_relative_pct,
        "Mediana": median,
        "Mínimo": minimum,
        "Máximo": maximum,
        "Rango": data_range,
        "IC95 inferior": ci_low,
        "IC95 superior": ci_high,
    }

def bubble_diameters(values, min_px=28.0, max_px=72.0):
    v = np.asarray(values, dtype=float)
    if len(v) == 1:
        return np.array([(min_px + max_px) / 2.0])

    if np.allclose(v, v[0]):
        return np.full(len(v), (min_px + max_px) / 2.0)

    vmin = float(np.min(v))
    vmax = float(np.max(v))
    relative_spread = (vmax - vmin) / vmin if vmin > 0 else float("inf")

    if relative_spread < 0.05:
        center = (min_px + max_px) / 2.0
        if np.ptp(v) == 0:
            return np.full(len(v), center)
        # deliberately modest visual spread when scientific values are nearly equal
        scaled = center + 8.0 * (v - np.mean(v)) / np.ptp(v)
        return np.clip(scaled, min_px, max_px)

    return min_px + (v - vmin) * (max_px - min_px) / (vmax - vmin)
