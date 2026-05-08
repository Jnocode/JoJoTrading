"""Stage 4 valuation helpers kept for legacy tests and scripts."""

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover - only used when streamlit is absent
    class _StreamlitFallback:
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return None

            return _noop

    st = _StreamlitFallback()


class Stage4IntegrationPanel:
    """Minimal Stage 4 panel logic used by the historical Streamlit tests."""

    def __init__(self):
        self.wacc_calculator = object()
        self.industry_map = {
            "semiconductor": "半導體",
            "electronics": "電子",
            "finance": "金融",
        }

    def _render_excel_import(self):
        uploaded_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
        if uploaded_file is None:
            return None

        df = pd.read_excel(uploaded_file)
        if len(df) > 1:
            st.info(f"📊 偵測到 {len(df)} 筆數據，切換至批次分析模式")

        if st.button("Calculate"):
            return df
        return None

    def _generate_pdf_report(self, stock_code, wacc_result, disposal_result, params_result):
        lines = [
            "JoJo Trading Stage 4 Report",
            f"Stock: {stock_code}",
            f"WACC: {wacc_result.get('wacc', 'N/A')}",
            f"Disposal: {disposal_result.get('has_disposal', 'N/A')}",
            f"Discount Rate: {params_result.get('discount_rate', 'N/A')}",
        ]
        return "\n".join(lines).encode("utf-8")

    def _render_sensitivity_analysis(self, base_wacc, base_growth, calculate_value):
        wacc_range = [base_wacc + delta for delta in (-0.02, -0.01, 0, 0.01, 0.02)]
        growth_range = [
            base_growth + delta for delta in (-0.01, -0.005, 0, 0.005, 0.01)
        ]
        matrix = [
            [calculate_value(wacc, growth) for growth in growth_range]
            for wacc in wacc_range
        ]
        df = pd.DataFrame(
            matrix,
            index=[f"{value:.1%}" for value in wacc_range],
            columns=[f"{value:.1%}" for value in growth_range],
        )
        st.dataframe(df.style.format("{:,.2f}"))
        return df

    def _render_valuation_waterfall(self, breakdown, shares):
        try:
            import plotly.graph_objects as go
        except ImportError:
            st.warning("請安裝 plotly 以查看瀑布圖")
            return None

        fig = go.Figure(
            go.Waterfall(
                x=["顯性期", "終值", "淨負債", "股權價值"],
                y=[
                    breakdown.get("pv_explicit", 0),
                    breakdown.get("pv_terminal", 0),
                    -breakdown.get("net_debt", 0),
                    breakdown.get("equity_value", 0),
                ],
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        return fig

    def _calculate_dcf_breakdown(
        self,
        base_fcf,
        shares,
        wacc,
        terminal_growth,
        short_term_growth,
        net_debt,
        net_income=0,
        depreciation=0,
        amortization=0,
        capex=0,
        use_detailed_fcf=False,
        projection_years=5,
    ):
        try:
            current_fcf = (
                net_income + depreciation + amortization - capex
                if use_detailed_fcf
                else base_fcf
            )
            projected = [
                current_fcf * ((1 + short_term_growth) ** year)
                for year in range(1, projection_years + 1)
            ]
            pv_explicit = sum(
                cash_flow / ((1 + wacc) ** index)
                for index, cash_flow in enumerate(projected, start=1)
            )
            spread = max(wacc - terminal_growth, 0.001)
            terminal_value = projected[-1] * (1 + terminal_growth) / spread
            pv_terminal = terminal_value / ((1 + wacc) ** projection_years)
            enterprise_value = pv_explicit + pv_terminal
            equity_value = enterprise_value - net_debt
            share_price = equity_value / shares if shares else 0
            return {
                "failed": False,
                "current_fcf": current_fcf,
                "pv_explicit": pv_explicit,
                "pv_terminal": pv_terminal,
                "enterprise_value": enterprise_value,
                "net_debt": net_debt,
                "equity_value": equity_value,
                "share_price": share_price,
            }
        except Exception as exc:
            return {"failed": True, "error": str(exc), "current_fcf": 0, "share_price": 0}

