from __future__ import annotations
from io import BytesIO
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from data_io import list_excel_sheets, read_table, extract_numeric_column
from stats_core import compute_statistics
from plots import make_plotly_chart, make_static_chart, figure_bytes

st.set_page_config(
    page_title="Exactitud–Precisión Experimental",
    page_icon="📊",
    layout="wide",
)

st.title("Exactitud–Precisión Experimental")
st.caption("Compara hasta tres series de mediciones experimentales de una misma magnitud.")

st.markdown(
    """
**Cómo leer el gráfico**

- Más a la izquierda → mayor exactitud.
- Más abajo → mayor precisión.
- Burbuja más pequeña → menor error global respecto al valor de referencia.

**RMSE — error global respecto al valor de referencia:** resume cuánto se alejan, en conjunto,
las mediciones del valor de referencia. Puede aumentar porque el promedio se aleja del valor esperado
(menor exactitud), porque las mediciones están más dispersas (menor precisión), o por ambas razones.
"""
)

st.divider()

st.subheader("1. Define la magnitud")

c1, c2, c3 = st.columns([1.5, 0.7, 0.9])

with c1:
    magnitude = st.text_input(
        "Nombre de la magnitud",
        placeholder="Ej.: Aceleración de gravedad"
    )

with c2:
    symbol = st.text_input(
        "Símbolo",
        placeholder="Ej.: g"
    )

with c3:
    unit = st.text_input(
        "Unidad",
        placeholder="Ej.: m/s²"
    )

reference = st.number_input(
    "Valor de referencia o valor aceptado",
    value=1.0,
    format="%.10g"
)

reference_is_zero = float(reference) == 0.0

if reference_is_zero:
    st.warning(
        "Como el valor de referencia es cero, no se calcularán porcentajes respecto de la referencia. "
        "El gráfico usará diferencias, desviación estándar y RMSE absolutos."
    )

st.subheader("2. Carga tus datos")

st.info(
    "Carga entre 1 y 3 archivos. Cada archivo puede contener varias columnas. "
    "Luego selecciona la columna que contiene las estimaciones experimentales de la magnitud."
)

uploads = st.file_uploader(
    "Archivos XLSX, CSV o TXT",
    type=["xlsx", "csv", "txt"],
    accept_multiple_files=True
)

if len(uploads) > 3:
    st.error("Puedes cargar como máximo 3 archivos.")
    st.stop()

datasets = []

for i, uploaded in enumerate(uploads, start=1):
    with st.container(border=True):
        st.markdown(f"### Medición {i}")

        name = st.text_input(
            "Nombre del conjunto",
            value=f"Medición {i}",
            key=f"name_{i}"
        )

        sheet = None
        decimal = "."

        if uploaded.name.lower().endswith(".xlsx"):
            try:
                sheets = list_excel_sheets(uploaded.getvalue())
                sheet = st.selectbox(
                    "Hoja del archivo",
                    sheets,
                    key=f"sheet_{i}"
                )
            except Exception as exc:
                st.error(f"No pude leer las hojas del archivo: {exc}")
                continue
        else:
            decimal_option = st.selectbox(
                "Separador decimal",
                ["Punto (.)", "Coma (,)"],
                key=f"decimal_{i}"
            )
            decimal = "." if decimal_option.startswith("Punto") else ","

        try:
            df = read_table(
                uploaded.name,
                uploaded.getvalue(),
                sheet_name=sheet,
                decimal=decimal
            )
        except Exception as exc:
            st.error(str(exc))
            continue

        st.dataframe(df.head(8), use_container_width=True, hide_index=True)

        column = st.selectbox(
            f"¿Qué columna contiene los valores de {symbol or magnitude or 'la magnitud'}?",
            [str(c) for c in df.columns],
            key=f"column_{i}"
        )

        extracted = extract_numeric_column(df, column)

        st.write(f"Valores numéricos válidos: {extracted['valid_count']}")

        if extracted["excluded_empty"]:
            st.warning(
                f"Celdas vacías excluidas: {extracted['excluded_empty']}"
            )

        if extracted["excluded_non_numeric"]:
            st.warning(
                f"Valores no numéricos o no finitos excluidos: {extracted['excluded_non_numeric']}"
            )

        if extracted["zero_count"]:
            st.caption(
                f"Valores iguales a cero: {extracted['zero_count']}. Se consideran datos válidos."
            )

        if extracted["valid_count"] < 2:
            st.error("Se necesitan al menos dos valores válidos.")
            continue

        datasets.append({
            "name": name.strip() or f"Medición {i}",
            "values": extracted["values"],
        })

if not datasets:
    st.info("Carga al menos un conjunto válido para realizar el análisis.")
    st.stop()

st.subheader("3. Resultados estadísticos")

summary_rows = []
extra_rows = []

for dataset in datasets:
    stats = compute_statistics(dataset["values"], reference)

    summary_rows.append({
        "Medición": dataset["name"],
        "N": stats["N"],
        "Promedio": stats["Promedio"],
        "Desviación estándar": stats["Desviación estándar"],
        "Diferencia con referencia": stats["Diferencia con referencia"],
        "Error relativo (%)": stats["Error relativo (%)"],
        "Dispersión relativa (%)": stats["Dispersión relativa (%)"],
        "RMSE": stats["RMSE"],
        "RMSE relativo (%)": stats["RMSE relativo (%)"],
    })

    extra_rows.append({
        "Medición": dataset["name"],
        "Mediana": stats["Mediana"],
        "Mínimo": stats["Mínimo"],
        "Máximo": stats["Máximo"],
        "Rango": stats["Rango"],
        "IC95 inferior": stats["IC95 inferior"],
        "IC95 superior": stats["IC95 superior"],
    })

summary_df = pd.DataFrame(summary_rows)
extra_df = pd.DataFrame(extra_rows)

if reference_is_zero:
    display_cols = [
        "Medición", "N", "Promedio", "Desviación estándar",
        "Diferencia con referencia", "RMSE"
    ]
else:
    display_cols = [
        "Medición", "N", "Promedio", "Desviación estándar",
        "Diferencia con referencia", "Error relativo (%)",
        "Dispersión relativa (%)", "RMSE", "RMSE relativo (%)"
    ]

st.dataframe(
    summary_df[display_cols].style.format(precision=6),
    use_container_width=True,
    hide_index=True
)

with st.expander("¿Cómo se calcularon estos valores?"):
    st.latex(r"\bar{x}=\frac{1}{N}\sum_{i=1}^{N}x_i")
    st.latex(r"s=\sqrt{\frac{1}{N-1}\sum_{i=1}^{N}(x_i-\bar{x})^2}")
    st.latex(r"RMSE=\sqrt{\frac{1}{N}\sum_{i=1}^{N}(x_i-x_{\mathrm{ref}})^2}")
    if not reference_is_zero:
        st.latex(r"E=100\frac{|\bar{x}-x_{\mathrm{ref}}|}{|x_{\mathrm{ref}}|}")
        st.latex(r"P=100\frac{s}{|x_{\mathrm{ref}}|}")
        st.latex(r"RMSE_{\mathrm{rel}}=100\frac{RMSE}{|x_{\mathrm{ref}}|}")
    st.latex(
        r"RMSE^2=(\bar{x}-x_{\mathrm{ref}})^2+\frac{N-1}{N}s^2"
    )
    st.write(
        "Esta última relación muestra por qué el RMSE combina información sobre exactitud y precisión."
    )

with st.expander("Ver estadística adicional"):
    st.dataframe(
        extra_df.style.format(precision=6),
        use_container_width=True,
        hide_index=True
    )

st.subheader("4. Gráfico Exactitud–Precisión")

fig = make_plotly_chart(summary_df, reference_is_zero=reference_is_zero)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "El tamaño de cada burbuja se reescala solo para facilitar la comparación visual. "
    "El valor cuantitativo real del RMSE aparece en la tabla y al pasar el cursor sobre la burbuja."
)

st.subheader("5. Descargar resultados")

csv_bytes = summary_df.to_csv(index=False).encode("utf-8-sig")

xlsx_buffer = BytesIO()
with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
    summary_df.to_excel(writer, sheet_name="Resumen", index=False)
    extra_df.to_excel(writer, sheet_name="Estadistica_adicional", index=False)
xlsx_buffer.seek(0)

static_fig = make_static_chart(summary_df, reference_is_zero=reference_is_zero)
png_bytes = figure_bytes(static_fig, fmt="png", dpi=300)
pdf_bytes = figure_bytes(static_fig, fmt="pdf")
plt.close(static_fig)

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.download_button(
        "Descargar CSV",
        data=csv_bytes,
        file_name="resumen_experimental.csv",
        mime="text/csv",
        use_container_width=True
    )

with d2:
    st.download_button(
        "Descargar Excel",
        data=xlsx_buffer.getvalue(),
        file_name="resultados_experimentales.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with d3:
    st.download_button(
        "Descargar PNG",
        data=png_bytes,
        file_name="grafico_exactitud_precision.png",
        mime="image/png",
        use_container_width=True
    )

with d4:
    st.download_button(
        "Descargar PDF",
        data=pdf_bytes,
        file_name="grafico_exactitud_precision.pdf",
        mime="application/pdf",
        use_container_width=True
    )
