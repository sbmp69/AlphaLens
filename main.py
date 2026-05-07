import customtkinter as ctk
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import threading
import time
import os
from datetime import datetime, timedelta
import requests
import webbrowser
import random
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.platypus import KeepTogether

# --- Theme Configuration ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG_COLOR = "#09090E"
PANEL_BG = "#13131F"
CARD_BG = "#1A1A27"
ACCENT_PURPLE = "#8B5CF6"
ACCENT_BLUE = "#3B82F6"
ACCENT_GREEN = "#10B981"
ACCENT_RED = "#EF4444"
ACCENT_YELLOW = "#F59E0B"
TEXT_LIGHT = "#F8FAFC"
TEXT_MUTED = "#64748B"
BORDER_COLOR = "#27273A"
FONT_FAMILY = "Helvetica"

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

def open_url(url):
    webbrowser.open_new(url)

def make_clickable(widget, url):
    widget.bind("<Button-1>", lambda e, u=url: open_url(u))
    try: widget.configure(cursor="hand2")
    except: pass

class PDFGenerator:
    # Reportlab color constants
    C_BG       = colors.HexColor("#09090E")
    C_PANEL    = colors.HexColor("#13131F")
    C_PURPLE   = colors.HexColor("#8B5CF6")
    C_BLUE     = colors.HexColor("#3B82F6")
    C_GREEN    = colors.HexColor("#10B981")
    C_RED      = colors.HexColor("#EF4444")
    C_YELLOW   = colors.HexColor("#F59E0B")
    C_WHITE    = colors.HexColor("#F8FAFC")
    C_MUTED    = colors.HexColor("#64748B")
    C_CARD     = colors.HexColor("#1A1A27")
    C_BORDER   = colors.HexColor("#27273A")

    @classmethod
    def _styles(cls):
        base = getSampleStyleSheet()
        styles = {
            "title": ParagraphStyle(
                "title", fontSize=28, textColor=cls.C_PURPLE, alignment=TA_CENTER,
                fontName="Helvetica-Bold", spaceAfter=4
            ),
            "subtitle": ParagraphStyle(
                "subtitle", fontSize=14, textColor=cls.C_MUTED, alignment=TA_CENTER,
                fontName="Helvetica", spaceAfter=2
            ),
            "section": ParagraphStyle(
                "section", fontSize=14, textColor=cls.C_WHITE, fontName="Helvetica-Bold",
                spaceBefore=14, spaceAfter=6
            ),
            "body": ParagraphStyle(
                "body", fontSize=11, textColor=cls.C_WHITE, fontName="Helvetica",
                leading=16, spaceAfter=4
            ),
            "muted": ParagraphStyle(
                "muted", fontSize=10, textColor=cls.C_MUTED, fontName="Helvetica",
                leading=14, spaceAfter=4
            ),
            "ai": ParagraphStyle(
                "ai", fontSize=11, textColor=cls.C_WHITE, fontName="Helvetica",
                leading=18, spaceAfter=0, leftIndent=8
            ),
        }
        return styles

    @classmethod
    def create_report(cls, save_path, ticker, price, change_pct, trend, breakout,
                      risk, sentiment, summary, vol, mcap, ma50, ma200, volat):
        """Generate a professional PDF report. Returns (True, path) or (False, error_msg)."""
        try:
            doc = SimpleDocTemplate(
                save_path,
                pagesize=A4,
                leftMargin=20*mm, rightMargin=20*mm,
                topMargin=22*mm, bottomMargin=22*mm
            )
            s = cls._styles()
            story = []

            # ── HEADER ──
            story.append(Paragraph("🔮 AlphaLens Market Report", s["title"]))
            story.append(Paragraph(f"Ticker: {ticker}", s["subtitle"]))
            story.append(Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}",
                s["muted"]
            ))
            story.append(Spacer(1, 8*mm))
            story.append(HRFlowable(width="100%", thickness=0.8, color=cls.C_PURPLE))
            story.append(Spacer(1, 6*mm))

            # ── SECTION: SUMMARY ──
            story.append(Paragraph("Market Summary", s["section"]))

            sign = "+" if change_pct >= 0 else ""
            trend_color = "#10B981" if trend == "Uptrend" else "#EF4444"
            risk_color  = "#EF4444" if risk == "High" else ("#F59E0B" if risk == "Medium" else "#10B981")
            sent_color  = "#10B981" if sentiment == "Positive" else ("#EF4444" if sentiment == "Negative" else "#F59E0B")

            summary_data = [
                [Paragraph("Metric", ParagraphStyle("h", fontSize=11, textColor=cls.C_MUTED, fontName="Helvetica-Bold")),
                 Paragraph("Value",  ParagraphStyle("h", fontSize=11, textColor=cls.C_MUTED, fontName="Helvetica-Bold"))],
                [Paragraph("Current Price", s["body"]),
                 Paragraph(f"${price:,.2f}  ({sign}{change_pct:.2f}%)", s["body"])],
                [Paragraph("Trend Status", s["body"]),
                 Paragraph(f'<font color="{trend_color}"><b>{trend}</b></font>', s["body"])],
                [Paragraph("Breakout Detected", s["body"]),
                 Paragraph(breakout, s["body"])],
                [Paragraph("Risk Profile", s["body"]),
                 Paragraph(f'<font color="{risk_color}"><b>{risk}</b></font>', s["body"])],
                [Paragraph("Market Sentiment", s["body"]),
                 Paragraph(f'<font color="{sent_color}"><b>{sentiment}</b></font>', s["body"])],
            ]

            tbl = Table(summary_data, colWidths=[80*mm, 90*mm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0),  cls.C_PANEL),
                ("BACKGROUND",  (0, 1), (-1, -1), cls.C_CARD),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [cls.C_CARD, cls.C_PANEL]),
                ("GRID",        (0, 0), (-1, -1),  0.4, cls.C_BORDER),
                ("TOPPADDING",  (0, 0), (-1, -1),  6),
                ("BOTTOMPADDING",(0,0), (-1, -1),  6),
                ("LEFTPADDING", (0, 0), (-1, -1),  10),
                ("RIGHTPADDING",(0, 0), (-1, -1),  10),
                ("ROUNDEDCORNERS", [4]),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 8*mm))

            # ── SECTION: KEY METRICS ──
            story.append(HRFlowable(width="100%", thickness=0.4, color=cls.C_BORDER))
            story.append(Paragraph("Key Metrics", s["section"]))

            metrics_data = [
                [Paragraph("Volume", s["muted"]),
                 Paragraph("Market Cap", s["muted"]),
                 Paragraph("MA (50 / 200)", s["muted"]),
                 Paragraph("Volatility", s["muted"])],
                [Paragraph(vol, s["body"]),
                 Paragraph(mcap, s["body"]),
                 Paragraph(f"{ma50} / {ma200}", s["body"]),
                 Paragraph(volat, s["body"])],
            ]
            m_tbl = Table(metrics_data, colWidths=[42*mm, 42*mm, 52*mm, 34*mm])
            m_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0),  cls.C_PANEL),
                ("BACKGROUND",  (0, 1), (-1, 1),  cls.C_CARD),
                ("GRID",        (0, 0), (-1, -1),  0.4, cls.C_BORDER),
                ("TOPPADDING",  (0, 0), (-1, -1),  6),
                ("BOTTOMPADDING",(0,0), (-1, -1),  6),
                ("LEFTPADDING", (0, 0), (-1, -1),  10),
                ("RIGHTPADDING",(0, 0), (-1, -1),  10),
                ("ALIGN",       (0, 0), (-1, -1),  "CENTER"),
            ]))
            story.append(m_tbl)
            story.append(Spacer(1, 8*mm))

            # ── SECTION: AI INSIGHTS ──
            story.append(HRFlowable(width="100%", thickness=0.4, color=cls.C_BORDER))
            story.append(Paragraph("AI Executive Insights", s["section"]))

            ai_box_data = [[Paragraph(summary, s["ai"])]]
            ai_tbl = Table(ai_box_data, colWidths=[170*mm])
            ai_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, -1), cls.C_CARD),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING",(0, 0), (-1, -1), 14),
                ("TOPPADDING",  (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING",(0,0), (-1, -1), 12),
                ("BOX",         (0, 0), (-1, -1),  0.8, cls.C_PURPLE),
            ]))
            story.append(ai_tbl)
            story.append(Spacer(1, 12*mm))

            # ── FOOTER ──
            story.append(HRFlowable(width="100%", thickness=0.8, color=cls.C_PURPLE))
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph(
                "Built for clarity. Designed for precision.  |  AlphaLens © 2025",
                ParagraphStyle("footer", fontSize=9, textColor=cls.C_MUTED,
                               fontName="Helvetica", alignment=TA_CENTER)
            ))

            # Background canvas callback for dark page
            def dark_bg(canvas, doc):
                canvas.saveState()
                canvas.setFillColor(cls.C_BG)
                canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
                canvas.restoreState()

            doc.build(story, onFirstPage=dark_bg, onLaterPages=dark_bg)
            return True, save_path

        except Exception as ex:
            return False, str(ex)

class DataEngine:
    @staticmethod
    def fetch_data(ticker, period):
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        info = stock.info
        return df, info

    @staticmethod
    def detect_breakout(df):
        df['Resistance'] = df['High'].rolling(window=20).max().shift(1)
        df['Breakout'] = df['Close'] > df['Resistance']
        return df
        
    @staticmethod
    def fetch_news(ticker):
        if not FINNHUB_API_KEY: return []
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
            url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200: return res.json()[:15]
        except: pass
        return []

    @staticmethod
    def analyze_sentiment(news_list):
        if not news_list: return "Neutral", TEXT_MUTED
        pos_words = ['up', 'growth', 'surge', 'jump', 'gain', 'buy', 'positive', 'beat', 'higher', 'bull', 'profit', 'dividend']
        neg_words = ['down', 'drop', 'fall', 'plunge', 'loss', 'sell', 'negative', 'miss', 'lower', 'bear', 'lawsuit', 'warning']
        score = 0
        for item in news_list:
            text = (item.get('headline', '') + ' ' + item.get('summary', '')).lower()
            for w in pos_words:
                if w in text: score += 1
            for w in neg_words:
                if w in text: score -= 1
        if score >= 3: return "Positive", ACCENT_GREEN
        elif score <= -3: return "Negative", ACCENT_RED
        else: return "Neutral", ACCENT_YELLOW

    @staticmethod
    def generate_ai_summary(trend, sentiment):
        if trend == "Uptrend" and sentiment == "Positive":
            return random.choice([
                "Strong bullish momentum driven by extremely favorable market sentiment.",
                "Technical indicators and news headlines strictly align, projecting a powerful upward trajectory.",
                "The asset is demonstrating robust strength, backed heavily by optimistic financial news."
            ])
        elif trend == "Downtrend" and sentiment == "Negative":
            return random.choice([
                "Bearish trend solidly confirmed by deteriorating market sentiment.",
                "Overwhelming negative news flow is accelerating the current downward technical pressure.",
                "Both technicals and fundamentals flash warning signs. Downward momentum is prevalent."
            ])
        else:
            return random.choice([
                "Mixed signals detected: Technical trends and fundamental sentiment are currently diverging.",
                "Market indecision: The asset's price action contradicts recent news sentiment. Proceed with caution.",
                "Volatility expected. Fundamental indicators and technical moving averages lack a unified direction."
            ])

    @staticmethod
    def load_csv(filepath):
        """Load and normalize a user-uploaded stock CSV. Returns (df, None) or (None, error_str)."""
        try:
            df = pd.read_csv(filepath)
            if df.empty:
                return None, "The CSV file is empty."
            col_map = {}
            for col in df.columns:
                lower = col.lower().strip()
                if lower in ['date', 'datetime', 'time', 'timestamp']:
                    col_map[col] = 'Date'
                elif lower in ['open', 'open price', 'open_price']:
                    col_map[col] = 'Open'
                elif lower in ['high', 'high price', 'high_price']:
                    col_map[col] = 'High'
                elif lower in ['low', 'low price', 'low_price']:
                    col_map[col] = 'Low'
                elif lower in ['close', 'close price', 'close_price', 'adj close', 'adj_close', 'adjusted close']:
                    col_map[col] = 'Close'
                elif lower in ['volume', 'vol']:
                    col_map[col] = 'Volume'
            df = df.rename(columns=col_map)
            # Drop duplicate columns (e.g. both 'Close' and 'Adj Close' map to 'Close')
            df = df.loc[:, ~df.columns.duplicated()]
            if 'Close' not in df.columns:
                return None, "Could not find a 'Close' price column.\nSupported names: Close, close, Adj Close, adjusted close."
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
                df = df.set_index('Date')
            df = df.sort_index()
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df = df.dropna(subset=['Close'])
            if df.empty:
                return None, "No valid numeric Close price data found after cleaning."
            if len(df) < 5:
                return None, f"Dataset too small ({len(df)} rows). At least 5 data points required."
            for col in ['Open', 'High', 'Low']:
                if col not in df.columns:
                    df[col] = df['Close']
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df['Close'])
            if 'Volume' not in df.columns:
                df['Volume'] = 0
            else:
                df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)
            return df, None
        except Exception as ex:
            return None, str(ex)

    @staticmethod
    def generate_ai_summary_from_data(df, trend, sentiment, risk, volatility):
        """Generate a dynamic, data-driven AI summary for uploaded datasets."""
        latest = float(df['Close'].iloc[-1])
        oldest = float(df['Close'].iloc[0])
        total_return = ((latest - oldest) / oldest) * 100
        recent_n = min(30, len(df))
        recent_prices = df['Close'].iloc[-recent_n:]
        recent_high = float(recent_prices.max())
        recent_low  = float(recent_prices.min())
        range_pct   = ((recent_high - recent_low) / recent_low) * 100 if recent_low != 0 else 0
        momentum_n  = min(10, len(df))
        mom_start   = float(df['Close'].iloc[-momentum_n])
        momentum    = ((latest - mom_start) / mom_start) * 100 if mom_start != 0 else 0
        parts = []
        if total_return >= 20:
            parts.append(f"Dataset indicates strong bullish momentum with a {total_return:.1f}% cumulative gain over the full period.")
        elif total_return >= 5:
            parts.append(f"Moderate upward drift detected — the dataset registers a {total_return:.1f}% net gain.")
        elif total_return <= -20:
            parts.append(f"Dataset reveals sustained bearish pressure, with prices declining {abs(total_return):.1f}% from start to end.")
        elif total_return <= -5:
            parts.append(f"A gradual downtrend is evident, posting a {abs(total_return):.1f}% net loss across the period.")
        else:
            parts.append(f"Price action is broadly range-bound with a negligible net change of {total_return:+.1f}%.")
        if volatility > 60:
            parts.append(f"Price action suggests extreme volatility ({volatility:.1f}% annualized) — high-risk, speculative behavior.")
        elif volatility > 40:
            parts.append(f"Elevated volatility at {volatility:.1f}% annualized implies significant price uncertainty and elevated risk.")
        elif volatility > 20:
            parts.append(f"Volatility ({volatility:.1f}% annualized) is within a moderate range, consistent with normal market fluctuations.")
        else:
            parts.append(f"Low volatility ({volatility:.1f}% annualized) reflects a stable, low-risk price environment.")
        if momentum >= 5:
            parts.append(f"Short-term momentum is positive (+{momentum:.1f}%), suggesting improving buying pressure.")
        elif momentum <= -5:
            parts.append(f"Short-term momentum is negative ({momentum:.1f}%), indicating recent selling pressure.")
        if range_pct > 20:
            parts.append(f"Recent price range spans {range_pct:.1f}% — aggressive price swings detected.")
        elif range_pct > 10:
            parts.append(f"Recent range of {range_pct:.1f}% indicates moderate but meaningful price oscillation.")
        return " ".join(parts)

    @staticmethod
    def fetch_market_strip():
        symbols = ['BTC-USD', 'ETH-USD', 'AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL']
        results = {}
        try:
            data = yf.download(symbols, period="5d", group_by='ticker', progress=False)
            for sym in symbols:
                try:
                    df = data[sym] if len(symbols) > 1 else data
                    if not df.empty and len(df) >= 2:
                        current = df['Close'].iloc[-1]
                        if isinstance(current, pd.Series): current = current.iloc[0]
                        prev = df['Close'].iloc[-2]
                        if isinstance(prev, pd.Series): prev = prev.iloc[0]
                        results[sym] = (current, ((current - prev) / prev) * 100)
                except: continue
        except: pass
        return results

class InsightEngine:
    """Computes 8 deep cross-variable insights from stock OHLCV data."""

    @classmethod
    def run_all(cls, df):
        has_vol  = 'Volume' in df.columns and df['Volume'].sum() > 0
        has_hl   = 'High' in df.columns and 'Low' in df.columns
        has_open = 'Open' in df.columns
        has_date = hasattr(df.index, 'day_name')
        n = len(df)
        if n < 60:
            return []
        runners = [
            (cls.day_of_week_effect,          has_date),
            (cls.monthly_seasonality,          has_date and n >= 365),
            (cls.volume_price_relationship,    has_vol and n >= 100),
            (cls.volatility_regime,            has_hl and n >= 100),
            (cls.gap_analysis,                 has_open and n >= 60),
            (cls.streak_analysis,              True),
            (cls.drawdown_profile,             n >= 100),
            (cls.anomaly_detection,            True),
        ]
        results = []
        for fn, cond in runners:
            if cond:
                try:
                    r = fn(df)
                    if r: results.append(r)
                except Exception as e:
                    print(f"Insight error [{fn.__name__}]: {e}")
        return results

    @classmethod
    def day_of_week_effect(cls, df):
        d = df.copy()
        d['R'] = d['Close'].pct_change() * 100
        d['Day'] = d.index.day_name()
        order = [x for x in ['Monday','Tuesday','Wednesday','Thursday','Friday'] if x in d['Day'].values]
        dow = d.groupby('Day')['R'].mean().reindex(order).dropna()
        if dow.empty: return None
        best, worst = dow.idxmax(), dow.idxmin()
        bv, wv = dow.max(), dow.min()
        spread = abs(bv - wv)
        sev = 'info' if spread < 0.05 else ('bullish' if bv > 0 else 'neutral')
        def cfn(fig, ax):
            colors = [ACCENT_GREEN if v >= 0 else ACCENT_RED for v in dow.values]
            bars = ax.barh(list(dow.index), list(dow.values), color=colors, alpha=0.85)
            ax.axvline(0, color=BORDER_COLOR, lw=1)
            ax.set_xlabel('Avg Daily Return (%)', color=TEXT_MUTED, fontsize=8)
            for bar, v in zip(bars, dow.values):
                ax.text(v + (0.005 if v >= 0 else -0.005), bar.get_y()+bar.get_height()/2,
                        f'{v:+.2f}%', va='center', ha='left' if v >= 0 else 'right',
                        color=TEXT_LIGHT, fontsize=8, fontweight='bold')
        return {'title':'Day-of-Week Effect','icon':'📅','severity':sev,'has_chart':True,'chart_fn':cfn,'chart_size':(4.5,2.5),
                'headline':f"{best} is strongest (+{bv:.2f}% avg); {worst} is weakest ({wv:.2f}%).",
                'detail':(f"A {spread:.2f}% performance spread exists between the best and worst trading days. "
                          f"This weekly rhythm is often driven by institutional rebalancing and options expiry cycles. "
                          f"Consistently timing entries on {worst} days and exits on {best} days is a known edge.")}

    @classmethod
    def monthly_seasonality(cls, df):
        d = df.copy()
        d['R'] = d['Close'].pct_change() * 100
        d['M'] = d.index.month
        names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
        mo = d.groupby('M')['R'].mean()
        mo.index = [names[i] for i in mo.index]
        best, worst = mo.idxmax(), mo.idxmin()
        bv, wv = mo.max(), mo.min()
        def cfn(fig, ax):
            colors = [ACCENT_GREEN if v >= 0 else ACCENT_RED for v in mo.values]
            ax.bar(list(mo.index), list(mo.values), color=colors, alpha=0.85)
            ax.axhline(0, color=BORDER_COLOR, lw=1)
            ax.set_ylabel('Avg Return (%)', color=TEXT_MUTED, fontsize=8)
            ax.tick_params(axis='x', rotation=45, labelsize=7)
        return {'title':'Monthly Seasonality','icon':'📆','severity':'bullish' if bv > 0 else 'bearish','has_chart':True,'chart_fn':cfn,'chart_size':(4.5,2.5),
                'headline':f"{best} is historically strongest (+{bv:.2f}%); {worst} weakest ({wv:.2f}%).",
                'detail':(f"Seasonal patterns in stock returns reflect earnings cycles, institutional calendar effects, "
                          f"and tax-loss selling. {best} consistently outperforms likely due to post-earnings momentum "
                          f"and fund inflows. {worst}'s weakness aligns with typical profit-taking and macro uncertainty periods.")}

    @classmethod
    def volume_price_relationship(cls, df):
        d = df.copy()
        d['R'] = d['Close'].pct_change()
        d['NR'] = d['R'].shift(-1)
        d = d.dropna()
        q90 = d['Volume'].quantile(0.9)
        hi = d[d['Volume'] >= q90]
        base_bull = (d['NR'] > 0).mean() * 100
        hi_bull   = (hi['NR'] > 0).mean() * 100
        diff = hi_bull - base_bull
        def cfn(fig, ax):
            cats = ['Normal Volume', 'High Volume\n(Top 10%)']
            vals = [base_bull, hi_bull]
            colors = [ACCENT_BLUE, ACCENT_GREEN if diff > 0 else ACCENT_RED]
            bars = ax.bar(cats, vals, color=colors, alpha=0.85, width=0.5)
            ax.axhline(50, color=ACCENT_YELLOW, lw=1, ls='--', alpha=0.7, label='50% baseline')
            ax.set_ylabel('% Next-day Positive', color=TEXT_MUTED, fontsize=8)
            ax.set_ylim(0, 100)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x()+bar.get_width()/2, v+1, f'{v:.0f}%', ha='center', color=TEXT_LIGHT, fontsize=10, fontweight='bold')
        sev = 'bullish' if diff > 5 else ('bearish' if diff < -5 else 'neutral')
        return {'title':'Volume → Price Signal','icon':'📦','severity':sev,'has_chart':True,'chart_fn':cfn,'chart_size':(3.8,2.5),
                'headline':f"High-volume days → next day rises {hi_bull:.0f}% of the time (vs {base_bull:.0f}% normally).",
                'detail':(f"When daily volume exceeds the 90th percentile, the subsequent session closes higher {hi_bull:.0f}% of the time — "
                          f"a {abs(diff):.1f}% {'bullish' if diff > 0 else 'bearish'} deviation from the {base_bull:.0f}% baseline. "
                          f"{'This signals institutional accumulation preceding rallies.' if diff > 0 else 'This signals distribution — large players offloading into strength.'}")}

    @classmethod
    def volatility_regime(cls, df):
        d = df.copy()
        d['Rng'] = (d['High'] - d['Low']) / d['Low'] * 100
        d = d.dropna(subset=['Rng'])
        curr = d['Rng'].iloc[-1]
        pct  = (d['Rng'] < curr).mean() * 100
        avg  = d['Rng'].mean()
        regime = 'LOW' if pct < 25 else ('HIGH' if pct > 75 else 'NORMAL')
        sev = 'info' if regime == 'LOW' else ('bearish' if regime == 'HIGH' else 'neutral')
        impl = ("Low-volatility compression historically precedes breakouts within 10–20 trading days." if regime == 'LOW'
                else "Elevated volatility signals market stress — risk management is critical." if regime == 'HIGH'
                else "Volatility is within historical norms — no unusual stress detected.")
        def cfn(fig, ax):
            ax.hist(d['Rng'].values, bins=40, color=ACCENT_PURPLE, alpha=0.7, edgecolor='none')
            ax.axvline(curr, color=ACCENT_GREEN, lw=2, label=f'Current: {curr:.2f}%')
            ax.axvline(avg, color=ACCENT_YELLOW, lw=1.5, ls='--', label=f'Mean: {avg:.2f}%')
            ax.set_xlabel('Intraday Range (%)', color=TEXT_MUTED, fontsize=8)
            ax.set_ylabel('Frequency', color=TEXT_MUTED, fontsize=8)
            ax.legend(fontsize=7, facecolor=PANEL_BG, edgecolor=BORDER_COLOR, labelcolor=TEXT_LIGHT)
        return {'title':'Volatility Regime','icon':'🌊','severity':sev,'has_chart':True,'chart_fn':cfn,'chart_size':(4.5,2.5),
                'headline':f"Volatility regime: {regime} — at {pct:.0f}th percentile historically.",
                'detail':f"Current intraday range ({curr:.2f}%) is at the {pct:.0f}th percentile of all {len(d)} trading days. Historical mean: {avg:.2f}%. {impl}"}

    @classmethod
    def gap_analysis(cls, df):
        d = df.copy()
        d['PrevC'] = d['Close'].shift(1)
        d['GapPct'] = (d['Open'] - d['PrevC']) / d['PrevC'] * 100
        d['DayR']   = (d['Close'] - d['Open']) / d['Open'] * 100
        d = d.dropna()
        gu = d[d['GapPct'] > 0]; gd = d[d['GapPct'] < 0]
        gu_pct = len(gu) / len(d) * 100
        cont_pct = (gu['DayR'] > 0).mean() * 100 if len(gu) > 10 else 50
        sev = 'bullish' if gu_pct > 52 and cont_pct > 55 else 'neutral'
        def cfn(fig, ax):
            wedges, texts, autos = ax.pie([len(gu), len(gd)], labels=['Gap Up', 'Gap Down'],
                colors=[ACCENT_GREEN, ACCENT_RED], autopct='%1.0f%%', startangle=90,
                textprops={'color': TEXT_LIGHT, 'fontsize': 9},
                wedgeprops={'edgecolor': PANEL_BG, 'linewidth': 2})
            for at in autos: at.set_color(TEXT_LIGHT)
        return {'title':'Overnight Gap Analysis','icon':'📈','severity':sev,'has_chart':True,'chart_fn':cfn,'chart_size':(3.5,2.5),
                'headline':f"Gaps up {gu_pct:.0f}% of sessions; {cont_pct:.0f}% of gap-ups continue intraday.",
                'detail':(f"This stock opens above the prior close {gu_pct:.0f}% of trading days. "
                          f"Of those gap-up sessions, {cont_pct:.0f}% close above the open — indicating a "
                          f"{'momentum bias (gaps continue)' if cont_pct > 55 else 'mean-reversion bias (gaps fill)'}. "
                          f"Avg gap magnitude: +{gu['GapPct'].mean():.2f}% up / {gd['GapPct'].mean():.2f}% down.")}

    @classmethod
    def streak_analysis(cls, df):
        d = df.copy()
        d['R'] = d['Close'].pct_change()
        d = d.dropna()
        streak, streaks = 0, []
        for v in (d['R'] > 0):
            streak = (streak + 1) if v else (streak - 1)
            streak = max(streak, 1) if v else min(streak, -1)
            streaks.append(streak)
        d['Streak'] = streaks
        rev = {}
        for t in [3, 4, 5]:
            idx = [i+1 for i,s in enumerate(streaks[:-1]) if s == t]
            if len(idx) >= 5:
                rev[t] = (d['R'].iloc[idx] < 0).mean() * 100
        max_up   = max(streaks)
        max_down = abs(min(streaks))
        curr_s   = streaks[-1]
        curr_txt = f"▲ {abs(curr_s)} up-days" if curr_s > 0 else f"▼ {abs(curr_s)} down-days"
        if rev:
            bt = max(rev, key=lambda k: abs(rev[k]-50))
            rv = rev[bt]
            sev = 'info' if abs(rv-50) < 10 else ('bearish' if rv > 65 else 'bullish')
            hl  = f"After {bt}+ consecutive up-days, next day reverses {rv:.0f}% of the time."
            det = (f"Mean-reversion signal: {rv:.0f}% reversal probability after {bt}+ green days (baseline ~50%). "
                   f"Longest up-streak: {max_up} days. Longest down-streak: {max_down} days. Current: {curr_txt}.")
        else:
            sev, hl = 'info', f"Longest up-streak: {max_up} days. Longest down-streak: {max_down} days."
            det = f"Current streak: {curr_txt}. Insufficient data for reversal probabilities."
        def cfn(fig, ax):
            if not rev: ax.text(0.5,0.5,'Insufficient data',ha='center',va='center',color=TEXT_MUTED,transform=ax.transAxes); return
            xs = [f"After {t}+\nup-days" for t in rev]
            ys = list(rev.values())
            colors = [ACCENT_RED if r > 55 else ACCENT_GREEN if r < 45 else ACCENT_YELLOW for r in ys]
            bars = ax.bar(xs, ys, color=colors, alpha=0.85, width=0.5)
            ax.axhline(50, color=ACCENT_YELLOW, lw=1, ls='--', alpha=0.7)
            ax.set_ylabel('Reversal %', color=TEXT_MUTED, fontsize=8)
            ax.set_ylim(0, 100)
            for bar, v in zip(bars, ys):
                ax.text(bar.get_x()+bar.get_width()/2, v+1, f'{v:.0f}%', ha='center', color=TEXT_LIGHT, fontsize=10, fontweight='bold')
        return {'title':'Streak & Reversal','icon':'🔁','severity':sev,'has_chart':bool(rev),'chart_fn':cfn,'chart_size':(3.8,2.5),
                'headline':hl,'detail':det}

    @classmethod
    def drawdown_profile(cls, df):
        d = df.copy()
        d['DD'] = (d['Close'] - d['Close'].cummax()) / d['Close'].cummax() * 100
        max_dd  = d['DD'].min()
        curr_dd = d['DD'].iloc[-1]
        sev = 'bearish' if curr_dd < -5 else ('bullish' if curr_dd > -2 else 'neutral')
        events = 0
        in_dd = False
        for v in d['DD']:
            if v <= -5 and not in_dd: in_dd = True; events += 1
            elif v > -1: in_dd = False
        def cfn(fig, ax):
            ax.fill_between(range(len(d)), d['DD'].values, 0, color=ACCENT_RED, alpha=0.35)
            ax.plot(range(len(d)), d['DD'].values, color=ACCENT_RED, lw=1)
            ax.axhline(0, color=BORDER_COLOR, lw=0.8)
            ax.axhline(-10, color=ACCENT_YELLOW, lw=0.8, ls='--', alpha=0.5)
            ax.axhline(curr_dd, color=ACCENT_GREEN, lw=1.2, ls=':', alpha=0.9)
            ax.set_ylabel('Drawdown (%)', color=TEXT_MUTED, fontsize=8)
            ax.set_xlabel('Trading Days', color=TEXT_MUTED, fontsize=8)
        return {'title':'Drawdown Profile','icon':'📉','severity':sev,'has_chart':True,'chart_fn':cfn,'chart_size':(4.5,2.5),
                'headline':f"Max drawdown: {max_dd:.1f}%. Currently {curr_dd:.1f}% from peak.",
                'detail':(f"{events} drawdown events ≥5% detected. Max peak-to-trough: {max_dd:.1f}%. "
                          f"Current price is {abs(curr_dd):.1f}% {'below' if curr_dd < 0 else 'at'} the dataset high. "
                          f"{'Recovery needed — currently in a drawdown.' if curr_dd < -5 else 'Near all-time highs — healthy price structure.'}")}

    @classmethod
    def anomaly_detection(cls, df):
        d = df.copy()
        d['R'] = d['Close'].pct_change() * 100
        d = d.dropna(subset=['R'])
        mean, std = d['R'].mean(), d['R'].std()
        d['Z'] = (d['R'] - mean) / std
        anom = d[d['Z'].abs() > 3].copy()
        if anom.empty: return None
        pos_n = (anom['Z'] > 0).sum()
        neg_n = (anom['Z'] < 0).sum()
        biggest = anom.loc[anom['R'].abs().idxmax()]
        try: ds = biggest.name.strftime('%b %d, %Y')
        except: ds = str(biggest.name)
        sev = 'info'
        def cfn(fig, ax):
            ax.scatter(range(len(d)), d['R'].values, color=ACCENT_BLUE, s=4, alpha=0.4, label='Daily returns')
            ax_idx = [d.index.get_loc(i) for i in anom.index if i in d.index]
            ax.scatter(ax_idx, anom['R'].values, color=ACCENT_RED, s=40, zorder=5, label='Anomaly (>3σ)')
            ax.axhline(0, color=BORDER_COLOR, lw=0.8)
            ax.axhline(mean+3*std, color=ACCENT_YELLOW, lw=0.8, ls='--', alpha=0.6)
            ax.axhline(mean-3*std, color=ACCENT_YELLOW, lw=0.8, ls='--', alpha=0.6)
            ax.set_ylabel('Daily Return (%)', color=TEXT_MUTED, fontsize=8)
            ax.legend(fontsize=7, facecolor=PANEL_BG, edgecolor=BORDER_COLOR, labelcolor=TEXT_LIGHT)
        return {'title':'Anomaly Detection','icon':'🚨','severity':sev,'has_chart':True,'chart_fn':cfn,'chart_size':(4.5,2.5),
                'headline':f"{len(anom)} anomalous trading days detected — {pos_n} positive, {neg_n} negative outliers.",
                'detail':(f"Statistical outliers (|z-score| > 3σ) on {len(anom)} days. "
                          f"Largest move: {biggest['R']:+.1f}% on {ds}. "
                          f"{'Positive outliers dominate — extreme rallies exceed crashes in frequency.' if pos_n > neg_n else 'Negative outliers dominate — this stock experiences sharper crashes than rallies.'}")}


class LoadingOverlay(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#09090E", corner_radius=0)
        self.lbl = ctk.CTkLabel(self, text="Analyzing Market Data.", font=ctk.CTkFont(size=28, weight="bold"), text_color=ACCENT_PURPLE)
        self.lbl.place(relx=0.5, rely=0.5, anchor="center")
        self._is_animating = False

    def start(self):
        self._is_animating = True
        self.tkraise()
        self._animate(0)
        
    def stop(self):
        self._is_animating = False
        self.place_forget()
        
    def _animate(self, count):
        if not self._is_animating: return
        dots = "." * (count % 4)
        self.lbl.configure(text=f"Analyzing Market Data{dots}")
        self.after(400, self._animate, count + 1)

class SummaryCard(ctk.CTkFrame):
    def __init__(self, master, title, icon, value="--", subtext="--", color=TEXT_LIGHT):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        self.grid_columnconfigure(1, weight=1)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(top_frame, text=icon, font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(top_frame, text=title, font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=TEXT_MUTED).pack(side="left")
        self.lbl_value = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"), text_color=color)
        self.lbl_value.pack(anchor="w", padx=15, pady=(0, 2))
        self.lbl_subtext = ctk.CTkLabel(self, text=subtext, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED)
        self.lbl_subtext.pack(anchor="w", padx=15, pady=(0, 15))
        
    def update_data(self, value, subtext, color=TEXT_LIGHT):
        self.lbl_value.configure(text=value, text_color=color)
        self.lbl_subtext.configure(text=subtext)

class CompactMetricCard(ctk.CTkFrame):
    def __init__(self, master, title, value="--"):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        self.lbl_title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED)
        self.lbl_title.pack(anchor="center", pady=(8, 0))
        self.lbl_value = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=TEXT_LIGHT)
        self.lbl_value.pack(anchor="center", pady=(2, 8))
        
    def update_data(self, value):
        self.lbl_value.configure(text=value)

class InsightCard(ctk.CTkFrame):
    def __init__(self, master, title, icon):
        super().__init__(master, fg_color=BG_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        self.pack(fill="x", pady=4)
        self.grid_columnconfigure(1, weight=1)
        self.icon_lbl = ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=18), width=35)
        self.icon_lbl.grid(row=0, column=0, rowspan=2, padx=(5, 5), pady=8)
        self.title_lbl = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED)
        self.title_lbl.grid(row=0, column=1, sticky="sw", pady=(8, 0))
        self.val_lbl = ctk.CTkLabel(self, text="Pending", font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=TEXT_LIGHT)
        self.val_lbl.grid(row=1, column=1, sticky="nw", pady=(0, 8))
        
    def update_data(self, value, color, icon_text=None):
        self.val_lbl.configure(text=value, text_color=color)
        if icon_text: self.icon_lbl.configure(text=icon_text, text_color=color)

class NewsCardGrid(ctk.CTkFrame):
    def __init__(self, master, news_item, is_top=False):
        bc = ACCENT_PURPLE if is_top else BORDER_COLOR
        super().__init__(master, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=bc)
        self.pack(fill="both", expand=True, pady=6, padx=5)
        
        url = news_item.get("url", "")
        self.bind("<Enter>", lambda e: self.configure(fg_color="#1E293B"))
        self.bind("<Leave>", lambda e: self.configure(fg_color=CARD_BG))
        make_clickable(self, url)
        
        headline = news_item.get("headline", "No Title")
        source = news_item.get("source", "Unknown")
        category = news_item.get("category", "")
        dt = datetime.fromtimestamp(news_item.get("datetime", 0))
        time_str = dt.strftime("%b %d, %H:%M")
        
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(15, 5))
        make_clickable(top_row, url)
        
        if category:
            pill = ctk.CTkFrame(top_row, fg_color="#312E81", corner_radius=10, height=20)
            pill.pack(side="left", padx=(0, 8))
            pill.pack_propagate(False)
            lbl_cat = ctk.CTkLabel(pill, text=category.upper(), font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"), text_color=ACCENT_PURPLE)
            lbl_cat.pack(padx=8, pady=0)
            make_clickable(pill, url)
            make_clickable(lbl_cat, url)
            
        lbl_src = ctk.CTkLabel(top_row, text=source, font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=TEXT_MUTED)
        lbl_src.pack(side="left")
        make_clickable(lbl_src, url)
        
        lbl_time = ctk.CTkLabel(top_row, text=time_str, font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=TEXT_MUTED)
        lbl_time.pack(side="right")
        make_clickable(lbl_time, url)
        
        fsize = 18 if is_top else 14
        wrap_l = 1000 if is_top else 350
        lbl_head = ctk.CTkLabel(self, text=headline, font=ctk.CTkFont(family=FONT_FAMILY, size=fsize, weight="bold"), text_color=TEXT_LIGHT, justify="left", wraplength=wrap_l)
        lbl_head.pack(anchor="w", padx=15, pady=(5, 8))
        make_clickable(lbl_head, url)
        
        summary = news_item.get("summary", "")
        if summary:
            trunc_len = 200 if is_top else 90
            if len(summary) > trunc_len: summary = summary[:trunc_len] + "..."
            lbl_desc = ctk.CTkLabel(self, text=summary, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED, justify="left", wraplength=wrap_l)
            lbl_desc.pack(anchor="w", padx=15, pady=(0, 15))
            make_clickable(lbl_desc, url)
        else:
            ctk.CTkFrame(self, fg_color="transparent", height=8).pack(fill="x")

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.current_data = None
        self.current_info = None
        self.current_ticker = ""
        self.current_news = []
        self.csv_mode = False
        self.csv_filepath = ""
        
        self.grid_columnconfigure(0, weight=1)
        
        self._build_top_controls()
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).grid(row=1, column=0, sticky="ew", pady=10) # Divider
        self._build_summary_row()
        self._build_main_analysis()
        self._build_metrics_row()
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).grid(row=5, column=0, sticky="ew", pady=20) # Divider
        self._build_bottom_news()
        
    def _build_top_controls(self):
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ctk.CTkLabel(ctrl_frame, text="Ticker:", font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))
        self.ticker_entry = ctk.CTkEntry(ctrl_frame, width=150, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=14), border_color=BORDER_COLOR)
        self.ticker_entry.pack(side="left")
        self.ticker_entry.insert(0, "AAPL")
        
        self.fetch_btn = ctk.CTkButton(
            ctrl_frame, text="Analyze", width=100, height=35, 
            fg_color=ACCENT_PURPLE, hover_color="#7C3AED", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            command=self.on_fetch_clicked
        )
        self.fetch_btn.pack(side="left", padx=10)

        ctk.CTkLabel(ctrl_frame, text="or", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))

        self.upload_btn = ctk.CTkButton(
            ctrl_frame, text="📂  Upload CSV", width=135, height=35,
            fg_color=CARD_BG, hover_color="#1E293B", border_width=1, border_color=ACCENT_BLUE,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color=ACCENT_BLUE,
            command=self.on_upload_clicked
        )
        self.upload_btn.pack(side="left", padx=(0, 10))

        self.file_label = ctk.CTkLabel(
            ctrl_frame, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED
        )
        self.file_label.pack(side="left", padx=(0, 10))

        self.export_btn = ctk.CTkButton(
            ctrl_frame, text="Export PDF", width=100, height=35, 
            fg_color=CARD_BG, hover_color="#1E293B", border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            command=self.on_export_clicked, state="disabled"
        )
        self.export_btn.pack(side="right", padx=10)

    def _build_summary_row(self):
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        self.summary_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.card_price = SummaryCard(self.summary_frame, "Total Price", "💰")
        self.card_price.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.card_change = SummaryCard(self.summary_frame, "Daily Change %", "📈")
        self.card_change.grid(row=0, column=1, sticky="ew", padx=10)
        self.card_trend = SummaryCard(self.summary_frame, "Trend Status", "📊")
        self.card_trend.grid(row=0, column=2, sticky="ew", padx=10)
        self.card_risk = SummaryCard(self.summary_frame, "Risk Level", "⚠️")
        self.card_risk.grid(row=0, column=3, sticky="ew", padx=(10, 0))

    def _build_main_analysis(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 15))
        
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=65) 
        main_frame.grid_columnconfigure(1, weight=35) 
        
        # --- LEFT: CHART PANEL ---
        self.chart_panel = ctk.CTkFrame(main_frame, fg_color=PANEL_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        self.chart_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chart_panel.grid_rowconfigure(1, weight=1)
        self.chart_panel.grid_columnconfigure(0, weight=1)
        
        chart_top = ctk.CTkFrame(self.chart_panel, fg_color="transparent")
        chart_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        
        self.chart_title = ctk.CTkLabel(chart_top, text="Price Chart", font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=TEXT_LIGHT)
        self.chart_title.pack(side="left")
        
        self.period_var = ctk.StringVar(value="1y")
        self.timeframe_seg = ctk.CTkSegmentedButton(
            chart_top, values=["1mo", "3mo", "6mo", "1y", "5y"], variable=self.period_var,
            command=lambda v: self.on_fetch_clicked() if self.ticker_entry.get() else None,
            selected_color=ACCENT_PURPLE, selected_hover_color="#7C3AED",
            unselected_color=CARD_BG, unselected_hover_color=BORDER_COLOR
        )
        self.timeframe_seg.pack(side="right")
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4), facecolor=PANEL_BG)
        self.ax.set_facecolor(PANEL_BG)
        self.ax.tick_params(colors=TEXT_MUTED)
        for spine in self.ax.spines.values(): spine.set_color(BORDER_COLOR)
        self.ax.grid(True, linestyle='--', alpha=0.05, color=TEXT_LIGHT)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_panel)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.ax.text(0.5, 0.5, "Awaiting Data", ha='center', va='center', color=TEXT_MUTED)
        self.canvas.draw()
        
        # --- RIGHT: INSIGHTS ---
        self.right_panel = ctk.CTkFrame(main_frame, fg_color=PANEL_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(self.right_panel, text="Market Insights", font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=TEXT_LIGHT).pack(anchor="w", padx=20, pady=(20, 10))
        
        cards_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        cards_frame.pack(fill="x", padx=15)
        
        self.ins_trend = InsightCard(cards_frame, "Trend", "〰️")
        self.ins_breakout = InsightCard(cards_frame, "Breakout", "⚡")
        self.ins_sentiment = InsightCard(cards_frame, "News Sentiment", "📰")
        
        summary_container = ctk.CTkFrame(self.right_panel, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        summary_container.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(summary_container, text="AI Summary", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=ACCENT_PURPLE).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.summary_text = ctk.CTkTextbox(summary_container, fg_color="transparent", text_color=TEXT_LIGHT, wrap="word", font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.summary_text.insert("0.0", "Initialize analysis to generate insights.")
        self.summary_text.configure(state="disabled")

    def _build_metrics_row(self):
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        self.metrics_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.metric_vol = CompactMetricCard(self.metrics_frame, "Volume")
        self.metric_vol.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.metric_cap = CompactMetricCard(self.metrics_frame, "Market Cap")
        self.metric_cap.grid(row=0, column=1, sticky="ew", padx=10)
        self.metric_ma = CompactMetricCard(self.metrics_frame, "MA (50 / 200)")
        self.metric_ma.grid(row=0, column=2, sticky="ew", padx=10)
        self.metric_volat = CompactMetricCard(self.metrics_frame, "Volatility (Ann.)")
        self.metric_volat.grid(row=0, column=3, sticky="ew", padx=(10, 0))

    def _build_bottom_news(self):
        self.bottom_news_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_news_frame.grid(row=6, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(self.bottom_news_frame, text="Market News", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=TEXT_LIGHT).pack(anchor="w", pady=(0, 15))
        
        self.news_grid_container = ctk.CTkFrame(self.bottom_news_frame, fg_color="transparent")
        self.news_grid_container.pack(fill="both", expand=True)

    def on_export_clicked(self):
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please analyze a ticker before exporting.")
            return

        # 1. Ask user where to save
        default_name = f"AlphaLens_Report_{self.current_ticker}.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save AlphaLens Report"
        )
        if not save_path:
            return  # User cancelled

        self.export_btn.configure(text="Exporting...", state="disabled")

        # 2. Gather all data
        latest_close = self.current_data['Close'].iloc[-1]
        prev         = self.current_data['Close'].iloc[-2]
        pct          = ((latest_close - prev) / prev) * 100
        latest_ma50  = self.current_data['MA50'].iloc[-1]
        latest_ma200 = self.current_data['MA200'].iloc[-1]
        trend        = "Uptrend" if latest_ma50 > latest_ma200 else "Downtrend"
        brk          = "Yes" if self.current_data['Breakout'].iloc[-5:].any() else "No"
        volat_val    = self.current_data['Returns'].std() * np.sqrt(252) * 100
        risk         = "High" if volat_val > 40 else "Medium" if volat_val > 20 else "Low"
        mcap         = self.current_info.get("marketCap", None) if self.current_info else None
        vol          = self.current_data['Volume'].iloc[-1]

        self.summary_text.configure(state="normal")
        summary_str = self.summary_text.get("0.0", "end").strip()
        self.summary_text.configure(state="disabled")

        # 3. Run export in thread to avoid freezing UI
        def _do_export():
            ok, result = PDFGenerator.create_report(
                save_path, self.current_ticker,
                latest_close, pct, trend, brk, risk,
                self.sentiment, summary_str,
                self.format_large_number(vol),
                self.format_large_number(mcap) if mcap else "N/A",
                f"{latest_ma50:.1f}", f"{latest_ma200:.1f}", f"{volat_val:.1f}%"
            )
            self.after(0, lambda: self._on_export_done(ok, result))

        threading.Thread(target=_do_export, daemon=True).start()

    def _on_export_done(self, ok, result):
        self.export_btn.configure(text="Export PDF", state="normal")
        if ok:
            messagebox.showinfo("Report Saved", f"✅ Report saved successfully!\n\n{result}")
            webbrowser.open(f"file://{result}")
        else:
            messagebox.showerror("Export Failed", f"❌ Could not save report:\n{result}")

    def on_fetch_clicked(self):
        ticker = self.ticker_entry.get().strip().upper()
        period = self.period_var.get()
        if not ticker: return

        # Reset CSV mode when user clicks Analyze
        self.csv_mode = False
        self.file_label.configure(text="")

        self.app.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.app.overlay.start()
        
        for widget in self.news_grid_container.winfo_children():
            widget.destroy()
            
        thread = threading.Thread(target=self._process_pipeline, args=(ticker, period))
        thread.start()

    def on_upload_clicked(self):
        filepath = filedialog.askopenfilename(
            title="Upload Stock Dataset",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not filepath:
            return
        self.csv_mode = True
        self.csv_filepath = filepath
        filename = os.path.basename(filepath)
        self.file_label.configure(text=f"📄 {filename}", text_color=ACCENT_BLUE)
        self.app.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.app.overlay.start()
        for widget in self.news_grid_container.winfo_children():
            widget.destroy()
        threading.Thread(target=self._process_csv_pipeline, args=(filepath, filename), daemon=True).start()

    def _process_csv_pipeline(self, filepath, filename):
        try:
            df, error = DataEngine.load_csv(filepath)
            if error or df is None:
                self.after(0, self.app.overlay.stop)
                self.after(0, lambda: messagebox.showerror(
                    "Invalid Dataset",
                    f"\u274c Could not load dataset:\n\n{error}"
                ))
                self.after(0, lambda: self.file_label.configure(text="\u26a0\ufe0f Load failed", text_color=ACCENT_RED))
                return
            display_name = filename.replace(".csv", "").replace("_", " ").upper()
            self.current_ticker = display_name
            df['Returns'] = df['Close'].pct_change()
            df['MA50']    = df['Close'].rolling(window=min(50, len(df))).mean()
            df['MA200']   = df['Close'].rolling(window=min(200, len(df))).mean()
            df = DataEngine.detect_breakout(df)
            self.current_data = df
            self.current_info = {}
            self.current_news = []
            self.sentiment = "Neutral"
            self.sentiment_color = ACCENT_YELLOW
            self.after(0, self.update_gui_with_data)
            self.after(100, lambda: self._show_csv_success(filename))
            self.after(150, lambda df=df, n=display_name: self.app.insights_view.populate_insights(df, n))
            self.after(500, lambda n=display_name: self.app.show_insight_toast(n))
        except Exception as e:
            print(f"CSV pipeline error: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Processing failed:\n{e}"))
        finally:
            self.after(0, self.app.overlay.stop)
            self.after(0, lambda: self.export_btn.configure(state="normal"))

    def _show_csv_success(self, filename):
        success_frame = ctk.CTkFrame(
            self.news_grid_container, fg_color="#0A2318",
            corner_radius=10, border_width=1, border_color=ACCENT_GREEN
        )
        success_frame.pack(fill="x", pady=(5, 5))
        top_row = ctk.CTkFrame(success_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(12, 4))
        ctk.CTkLabel(
            top_row, text="\u2705  Dataset loaded successfully",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color=ACCENT_GREEN
        ).pack(side="left")
        ctk.CTkLabel(
            top_row, text=filename,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED
        ).pack(side="right")
        ctk.CTkLabel(
            success_frame,
            text="News sentiment is unavailable for uploaded datasets. AI insights are generated from price data only.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED, justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 12))

    def _process_pipeline(self, ticker, period):
        try:
            df, info = DataEngine.fetch_data(ticker, period)
            if df.empty:
                self.after(0, self.app.overlay.stop)
                return
                
            self.current_ticker = ticker
            df['Returns'] = df['Close'].pct_change()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            df = DataEngine.detect_breakout(df)
            
            news = DataEngine.fetch_news(ticker)
            sentiment, sentiment_color = DataEngine.analyze_sentiment(news)
            
            self.current_data = df
            self.current_info = info
            self.current_news = news
            self.sentiment = sentiment
            self.sentiment_color = sentiment_color
            
            self.after(0, self.update_gui_with_data)
            self.after(0, self.app.news_view.populate_news, news, ticker)
            self.after(50, lambda df=df, t=ticker: self.app.insights_view.populate_insights(df, t))
            self.after(400, lambda t=ticker: self.app.show_insight_toast(t))
            
        except Exception as e:
            print(f"Error processing: {e}")
        finally:
            self.after(0, self.app.overlay.stop)
            self.after(0, lambda: self.export_btn.configure(state="normal"))

    def format_large_number(self, num):
        if not num or num == "N/A" or np.isnan(num): return "--"
        if num >= 1e12: return f"{num/1e12:.2f}T"
        if num >= 1e9: return f"{num/1e9:.2f}B"
        if num >= 1e6: return f"{num/1e6:.2f}M"
        return f"{num:,.0f}"

    def update_gui_with_data(self):
        df = self.current_data
        if df is None or df.empty: return
        
        latest_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2] if len(df) > 1 else latest_close
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100
        
        color_change = ACCENT_GREEN if change >= 0 else ACCENT_RED
        sign = "+" if change >= 0 else ""
        
        self.card_price.update_data(f"${latest_close:,.2f}", f"Ticker: {self.current_ticker}", TEXT_LIGHT)
        self.card_change.update_data(f"{sign}{pct_change:.2f}%", f"{sign}{change:.2f} USD", color_change)
        
        latest_ma50 = df['MA50'].iloc[-1]
        latest_ma200 = df['MA200'].iloc[-1]
        
        trend = "Neutral"
        trend_color = TEXT_MUTED
        if not np.isnan(latest_ma50) and not np.isnan(latest_ma200):
            if latest_ma50 > latest_ma200:
                trend, trend_color = "Uptrend", ACCENT_GREEN
            else:
                trend, trend_color = "Downtrend", ACCENT_RED
                
        self.card_trend.update_data(trend, "MA50 vs MA200", trend_color)
        
        volatility = df['Returns'].std() * np.sqrt(252) * 100
        risk_level = "High" if volatility > 40 else "Medium" if volatility > 20 else "Low"
        risk_color = ACCENT_RED if risk_level == "High" else ACCENT_YELLOW if risk_level == "Medium" else ACCENT_GREEN
        self.card_risk.update_data(risk_level, "Annualized", risk_color)
        
        self.ax.clear()
        self.ax.tick_params(colors=TEXT_MUTED, labelsize=9)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['bottom'].set_color(BORDER_COLOR)
        self.ax.grid(True, linestyle='--', alpha=0.05, color=TEXT_LIGHT)
        
        dates = df.index
        self.ax.plot(dates, df['Close'], color=ACCENT_BLUE, linewidth=6, alpha=0.1)
        self.ax.plot(dates, df['Close'], color=ACCENT_BLUE, linewidth=2)
        self.ax.fill_between(dates, df['Close'], df['Close'].min() * 0.95, color=ACCENT_BLUE, alpha=0.08)
        
        if not df['MA50'].isna().all():
            self.ax.plot(dates, df['MA50'], color=ACCENT_PURPLE, linewidth=1, linestyle="--", alpha=0.6)
            
        breakouts = df[df['Breakout'] == True]
        if not breakouts.empty:
            self.ax.scatter(breakouts.index, breakouts['Close'], color=ACCENT_GREEN, marker='o', s=25, zorder=5, alpha=0.8)
            
        self.ax.axhline(y=latest_close, color=ACCENT_GREEN, linestyle=':', linewidth=1.5, alpha=0.6)
        self.ax.text(dates[-1], latest_close, f" ${latest_close:.2f} ", color=ACCENT_GREEN, fontsize=9, 
                     va='bottom', ha='right', fontweight='bold', 
                     bbox=dict(facecolor=PANEL_BG, edgecolor=ACCENT_GREEN, alpha=0.9, boxstyle='round,pad=0.2'))
        
        locator = mdates.AutoDateLocator(minticks=4, maxticks=7)
        formatter = mdates.ConciseDateFormatter(locator)
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)
        self.ax.set_ylim(df['Close'].min() * 0.95, df['Close'].max() * 1.05)
        
        self.chart_title.configure(text=f"{self.current_ticker} Price Chart")
        self.fig.tight_layout()
        self.canvas.draw()
        
        trend_icon = "↗" if trend == "Uptrend" else "↘" if trend == "Downtrend" else "〰️"
        self.ins_trend.update_data(trend, trend_color, trend_icon)
        
        recent_breakout = df['Breakout'].iloc[-5:].any()
        brk_text = "Yes" if recent_breakout else "No"
        brk_color = ACCENT_GREEN if recent_breakout else TEXT_MUTED
        self.ins_breakout.update_data(brk_text, brk_color, "⚡")
        self.ins_sentiment.update_data(self.sentiment, self.sentiment_color, "📰")
        
        if self.csv_mode:
            summary = DataEngine.generate_ai_summary_from_data(df, trend, self.sentiment, risk_level, volatility)
        else:
            summary = DataEngine.generate_ai_summary(trend, self.sentiment)
        self.summary_text.configure(state="normal")
        self.summary_text.delete("0.0", "end")
        self.summary_text.insert("0.0", summary)
        self.summary_text.configure(state="disabled")
        
        vol = df['Volume'].iloc[-1]
        mcap = self.current_info.get("marketCap", None) if self.current_info else None
        self.metric_vol.update_data(self.format_large_number(vol))
        self.metric_cap.update_data(self.format_large_number(mcap) if mcap else "N/A")
        ma_str = f"{latest_ma50:.1f} / {latest_ma200:.1f}" if not np.isnan(latest_ma50) and not np.isnan(latest_ma200) else "N/A"
        self.metric_ma.update_data(ma_str)
        self.metric_volat.update_data(f"{volatility:.1f}%")
        
        if self.csv_mode:
            pass  # Success banner is rendered by _show_csv_success()
        elif not FINNHUB_API_KEY:
            ctk.CTkLabel(self.news_grid_container, text="No API Key (FINNHUB_API_KEY)", text_color=TEXT_MUTED).pack(pady=10)
        else:
            if not self.current_news:
                ctk.CTkLabel(self.news_grid_container, text="No news found.", text_color=TEXT_MUTED).pack(pady=10)
            else:
                self.news_grid_container.grid_columnconfigure((0, 1, 2), weight=1)
                top_wrap = ctk.CTkFrame(self.news_grid_container, fg_color="transparent")
                top_wrap.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
                NewsCardGrid(top_wrap, self.current_news[0], is_top=True)
                for i, item in enumerate(self.current_news[1:7]):
                    row = 1 + (i // 3)
                    col = i % 3
                    card_wrap = ctk.CTkFrame(self.news_grid_container, fg_color="transparent")
                    card_wrap.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
                    NewsCardGrid(card_wrap, item, is_top=False)


class NewsView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.title = ctk.CTkLabel(self, text="Market News", font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"), text_color=TEXT_LIGHT)
        self.title.pack(anchor="w", pady=(20, 20), padx=20)
        self.news_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.news_frame.pack(fill="both", expand=True, padx=20)
        ctk.CTkLabel(self.news_frame, text="Analyze a ticker in Dashboard to view news.", text_color=TEXT_MUTED).pack(pady=40)

    def populate_news(self, news_list, ticker):
        for widget in self.news_frame.winfo_children(): widget.destroy()
        self.title.configure(text=f"Market News: {ticker}")
        if not FINNHUB_API_KEY:
            ctk.CTkLabel(self.news_frame, text="FINNHUB_API_KEY is not set.", text_color=ACCENT_RED).pack(pady=40)
            return
        if not news_list:
            ctk.CTkLabel(self.news_frame, text=f"No recent news found for {ticker}.", text_color=TEXT_MUTED).pack(pady=40)
            return
            
        featured = news_list[0]
        f_card = ctk.CTkFrame(self.news_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        f_card.pack(fill="x", pady=(0, 20))
        url = featured.get("url", "")
        make_clickable(f_card, url)
        f_card.bind("<Enter>", lambda e, c=f_card: c.configure(fg_color="#1E293B"))
        f_card.bind("<Leave>", lambda e, c=f_card: c.configure(fg_color=CARD_BG))
        
        ctk.CTkLabel(f_card, text="Featured Story", text_color=ACCENT_PURPLE, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        lbl_head = ctk.CTkLabel(f_card, text=featured.get('headline', ''), font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_LIGHT, justify="left", wraplength=1000)
        lbl_head.pack(anchor="w", padx=20, pady=5)
        make_clickable(lbl_head, url)
        
        dt = datetime.fromtimestamp(featured.get("datetime", 0))
        ctk.CTkLabel(f_card, text=f"{featured.get('source', '')} • {dt.strftime('%B %d, %Y %H:%M')}", text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(5, 20))
        
        grid_frame = ctk.CTkFrame(self.news_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure((0,1), weight=1)
        
        for i, item in enumerate(news_list[1:]):
            row, col = i // 2, i % 2
            n_card = ctk.CTkFrame(grid_frame, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            n_card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            url2 = item.get("url", "")
            make_clickable(n_card, url2)
            n_card.bind("<Enter>", lambda e, c=n_card: c.configure(fg_color="#1E293B"))
            n_card.bind("<Leave>", lambda e, c=n_card: c.configure(fg_color=CARD_BG))
            
            lbl_h2 = ctk.CTkLabel(n_card, text=item.get('headline', ''), font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_LIGHT, justify="left", wraplength=450)
            lbl_h2.pack(anchor="w", padx=15, pady=(15, 5))
            make_clickable(lbl_h2, url2)
            
            dt2 = datetime.fromtimestamp(item.get("datetime", 0))
            ctk.CTkLabel(n_card, text=f"{item.get('source', '')} • {dt2.strftime('%b %d')}", text_color=TEXT_MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 15))


class WatchlistView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        ctk.CTkLabel(self, text="Portfolio Watchlist", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_LIGHT).pack(anchor="w", padx=40, pady=(40, 20))
        
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=40)
        grid.grid_columnconfigure((0,1,2), weight=1)
        
        stocks = [
            ("AAPL", "Apple Inc.", 175.25, 1.25),
            ("TSLA", "Tesla Inc.", 180.10, -2.30),
            ("BTC-USD", "Bitcoin", 65400.00, 3.45),
            ("MSFT", "Microsoft Corp.", 410.50, 0.85),
            ("NVDA", "Nvidia Corp.", 890.20, 5.20),
            ("AMZN", "Amazon", 185.40, -0.45)
        ]
        
        for i, (tick, name, price, change) in enumerate(stocks):
            r, c = i//3, i%3
            card = ctk.CTkFrame(grid, fg_color=PANEL_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=r, column=c, sticky="nsew", padx=15, pady=15)
            card.bind("<Enter>", lambda e, cr=card: cr.configure(border_color=ACCENT_PURPLE))
            card.bind("<Leave>", lambda e, cr=card: cr.configure(border_color=BORDER_COLOR))
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=20, pady=(20, 5))
            ctk.CTkLabel(top, text=tick, font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_LIGHT).pack(side="left")
            
            color = ACCENT_GREEN if change > 0 else ACCENT_RED
            sign = "+" if change > 0 else ""
            ctk.CTkLabel(top, text=f"${price:,.2f}", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_LIGHT).pack(side="right")
            
            bot = ctk.CTkFrame(card, fg_color="transparent")
            bot.pack(fill="x", padx=20, pady=(0, 20))
            ctk.CTkLabel(bot, text=name, font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).pack(side="left")
            
            pill = ctk.CTkFrame(bot, fg_color="#1E293B", corner_radius=8)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=f"{sign}{change}%", font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(padx=8, pady=2)


class HowItWorksView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="How AlphaLens Works", font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"), text_color=ACCENT_PURPLE).pack(pady=(40, 30))
        container = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=100, pady=(0, 40))
        
        steps = [
            ("1. Data Fetching", "📡", "Fetches live price data via yfinance and corporate news via Finnhub API."),
            ("2. Trend Analysis", "📈", "Calculates short and long-term Moving Averages to ascertain primary market direction."),
            ("3. Breakout Detection", "⚡", "Monitors rolling 20-day resistance levels. Flags a breakout when price closes above resistance."),
            ("4. Sentiment Analysis", "📰", "Analyzes live news headlines scanning for financial keywords to determine Market Sentiment."),
            ("5. AI Synthesis", "🧠", "Combines trend momentum and sentiment into an actionable, rule-based output summary.")
        ]
        for title_txt, icon, desc in steps:
            step_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            step_card.pack(fill="x", padx=40, pady=15)
            ctk.CTkLabel(step_card, text=icon, font=ctk.CTkFont(size=32), text_color=ACCENT_BLUE).pack(side="left", padx=25, pady=20)
            text_frame = ctk.CTkFrame(step_card, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, pady=15)
            ctk.CTkLabel(text_frame, text=title_txt, font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=TEXT_LIGHT, anchor="w").pack(fill="x")
            ctk.CTkLabel(text_frame, text=desc, font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=TEXT_MUTED, anchor="w", justify="left", wraplength=700).pack(fill="x", pady=(5,0))


class AboutView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(expand=True, padx=80, pady=20)
        
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))
        ctk.CTkLabel(header_frame, text="About AlphaLens", font=ctk.CTkFont(family=FONT_FAMILY, size=34, weight="bold"), text_color=TEXT_LIGHT).pack()
        ctk.CTkLabel(header_frame, text="See Beyond the Market", font=ctk.CTkFont(family=FONT_FAMILY, size=16), text_color=ACCENT_PURPLE).pack(pady=(5, 0))
        
        intro_text = "AlphaLens is a financial intelligence dashboard that transforms raw market data into actionable insights using advanced analysis and real-time information."
        ctk.CTkLabel(main_container, text=intro_text, font=ctk.CTkFont(family=FONT_FAMILY, size=15), text_color=TEXT_MUTED, justify="center", wraplength=700).pack(pady=(20, 40))
        
        ctk.CTkLabel(main_container, text="Core Capabilities", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=TEXT_LIGHT).pack(anchor="w", pady=(0, 15))
        features_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        features_frame.pack(fill="x", pady=(0, 40))
        features_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        features = [
            ("📊", "Smart Analysis", "Trend detection & breakout insights"),
            ("📰", "News Intelligence", "Real-time market news & sentiment"),
            ("⚡", "Fast Processing", "Real-time API-driven insights"),
            ("🎯", "Clear Decisions", "Simple, readable summaries")
        ]
        for i, (icon, title, desc) in enumerate(features):
            card = ctk.CTkFrame(features_frame, fg_color=PANEL_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=0, column=i, sticky="nsew", padx=8)
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=32)).pack(pady=(25, 10))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"), text_color=TEXT_LIGHT).pack(pady=(0, 5))
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED, justify="center", wraplength=160).pack(padx=15, pady=(0, 25))
            
        ctk.CTkLabel(main_container, text="Technology Stack", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=TEXT_LIGHT).pack(anchor="w", pady=(0, 15))
        tech_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        tech_frame.pack(fill="x", pady=(0, 40))
        tech_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        tech_stack = [
            ("🐍", "Python", "Core Logic"),
            ("🖥️", "Tkinter", "Modern GUI"),
            ("📈", "Matplotlib", "Financial Charting"),
            ("📡", "yfinance", "Stock Data"),
            ("🌍", "Finnhub API", "News & Data")
        ]
        for i, (icon, title, desc) in enumerate(tech_stack):
            card = ctk.CTkFrame(tech_frame, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=0, column=i, sticky="nsew", padx=6)
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=15, pady=(15, 5))
            ctk.CTkLabel(top_row, text=icon, font=ctk.CTkFont(size=22)).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(top_row, text=title, font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=TEXT_LIGHT).pack(side="left")
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(0, 15))
            
        final_frame = ctk.CTkFrame(main_container, fg_color="#1E293B", corner_radius=12, border_width=1, border_color=ACCENT_PURPLE)
        final_frame.pack(pady=(10, 40))
        ctk.CTkLabel(final_frame, text="Built for clarity. Designed for precision.", font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold", slant="italic"), text_color=ACCENT_PURPLE).pack(padx=50, pady=25)


class InsightsView(ctk.CTkScrollableFrame):
    """Displays the 8 deep insight cards with embedded charts."""
    SEV_COLORS = {
        'bullish': ACCENT_GREEN, 'bearish': ACCENT_RED,
        'neutral': ACCENT_YELLOW, 'info': ACCENT_BLUE
    }
    SEV_LABELS = {
        'bullish': '🟢 Bullish', 'bearish': '🔴 Bearish',
        'neutral': '🟡 Neutral', 'info': '🔵 Informational'
    }

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 5))
        ctk.CTkLabel(hdr, text="🔍  Deep Market Insights",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=TEXT_LIGHT).pack(side="left")
        self.ticker_lbl = ctk.CTkLabel(hdr, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=TEXT_MUTED)
        self.ticker_lbl.pack(side="right")
        ctk.CTkLabel(self, text="Cross-variable statistical patterns hidden in the price data.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=30, pady=(0, 20))
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=25)
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)
        self._show_placeholder()

    def _show_placeholder(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.grid_frame,
            text="Analyze a ticker or upload a CSV to generate deep insights.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14), text_color=TEXT_MUTED
        ).grid(row=0, column=0, columnspan=2, pady=60)

    def populate_insights(self, df, ticker):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.ticker_lbl.configure(text=f"Ticker: {ticker}")
        insights = InsightEngine.run_all(df)
        self.last_insight_count = len(insights)
        if not insights:
            ctk.CTkLabel(self.grid_frame,
                text="Not enough data to generate insights (minimum 60 rows required).",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=TEXT_MUTED
            ).grid(row=0, column=0, columnspan=2, pady=60)
            return
        for i, ins in enumerate(insights):
            row, col = divmod(i, 2)
            card = self._make_card(ins)
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)


    def _make_card(self, ins):
        sev_color = self.SEV_COLORS.get(ins['severity'], ACCENT_BLUE)
        card = ctk.CTkFrame(self.grid_frame, fg_color=CARD_BG, corner_radius=14,
            border_width=1, border_color=sev_color)
        # Header row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(hdr, text=f"{ins['icon']}  {ins['title']}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT).pack(side="left")
        sev_pill = ctk.CTkFrame(hdr, fg_color=PANEL_BG, corner_radius=8)
        sev_pill.pack(side="right")
        ctk.CTkLabel(sev_pill, text=self.SEV_LABELS.get(ins['severity'], ''),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=sev_color).pack(padx=8, pady=2)
        # Headline
        ctk.CTkLabel(card, text=ins['headline'],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT, justify="left", wraplength=560
        ).pack(anchor="w", padx=16, pady=(4, 2))
        # Detail
        ctk.CTkLabel(card, text=ins['detail'],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED, justify="left", wraplength=560
        ).pack(anchor="w", padx=16, pady=(0, 8))
        # Embedded chart
        if ins.get('has_chart') and ins.get('chart_fn'):
            w, h = ins.get('chart_size', (4.5, 2.5))
            fig, ax = plt.subplots(figsize=(w, h), facecolor=PANEL_BG)
            ax.set_facecolor(PANEL_BG)
            ax.tick_params(colors=TEXT_MUTED, labelsize=8)
            for sp in ax.spines.values(): sp.set_color(BORDER_COLOR)
            try:
                ins['chart_fn'](fig, ax)
            except Exception as e:
                print(f"Chart render error: {e}")
            fig.tight_layout(pad=0.8)
            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 14))
            plt.close(fig)
        return card


class InsightToast(ctk.CTkFrame):
    """Premium slide-in corner notification directing user to the Insights tab."""
    def __init__(self, master, ticker, n_insights, on_click):
        super().__init__(master, fg_color="#161226", corner_radius=16,
                         border_width=1, border_color="#4A3480", width=340)
        self._master = master
        self._auto_id = None
        self._y = 1.1
        self._animating = True

        # ── Left purple accent bar (stays within border-radius, no overflow) ──
        ctk.CTkFrame(self, fg_color=ACCENT_PURPLE, width=5, corner_radius=0
        ).pack(side="left", fill="y")

        # ── Main content area ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(12, 14), pady=14)

        # Top row: icon + title + close button
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="✦", font=ctk.CTkFont(size=16),
            text_color=ACCENT_PURPLE).pack(side="left", padx=(0, 7))
        ctk.CTkLabel(top, text="Insights Ready",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT).pack(side="left")
        # Visible X button with its own pill background
        ctk.CTkButton(top, text="✕", width=28, height=28,
            fg_color="#2D2050", hover_color="#3D2F68",
            text_color="#C4B5FD", font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8, border_width=1, border_color="#5B4A9A",
            command=self.dismiss).pack(side="right")

        # Ticker + pattern count badges
        badges = ctk.CTkFrame(body, fg_color="transparent")
        badges.pack(fill="x", pady=(10, 0))
        short = (ticker[:16] + "\u2026") if len(ticker) > 16 else ticker
        tp = ctk.CTkFrame(badges, fg_color="#231840", corner_radius=6)
        tp.pack(side="left")
        ctk.CTkLabel(tp, text=f"  {short}  ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color="#C4B5FD").pack(padx=2, pady=3)
        ip = ctk.CTkFrame(badges, fg_color="#0C2416", corner_radius=6)
        ip.pack(side="left", padx=(6, 0))
        ctk.CTkLabel(ip, text=f"  ● {n_insights} patterns  ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=ACCENT_GREEN).pack(padx=2, pady=3)

        # Divider
        ctk.CTkFrame(body, fg_color="#2D2050", height=1).pack(fill="x", pady=(10, 8))

        # Subtitle
        ctk.CTkLabel(body,
            text="Cross-variable patterns hidden in the\nprice data are ready to explore.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#94A3B8", justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # CTA button
        ctk.CTkButton(body, text="View Deep Insights  \u2192", height=36,
            fg_color=ACCENT_PURPLE, hover_color="#7C3AED",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            corner_radius=8,
            command=lambda: [on_click(), self.dismiss()]
        ).pack(fill="x")

        # Animate in from below screen
        self.place(relx=0.99, rely=1.1, anchor="se")
        master.after(80, self._slide_in)
        self._auto_id = master.after(120000, self.dismiss)  # 2 minutes

    def _slide_in(self):
        if not self._animating: return
        target = 0.965
        if self._y > target:
            self._y = max(self._y - 0.02, target)
            try:
                self.place(relx=0.99, rely=self._y, anchor="se")
                self._master.after(12, self._slide_in)
            except: pass

    def dismiss(self):
        self._animating = False
        if self._auto_id:
            try: self._master.after_cancel(self._auto_id)
            except: pass
            self._auto_id = None
        self._slide_out()

    def _slide_out(self):
        if self._y < 1.12:
            self._y += 0.022
            try:
                self.place(relx=0.99, rely=self._y, anchor="se")
                self._master.after(12, self._slide_out)
            except: pass
        else:
            try: self.destroy()
            except: pass


class AlphaLensApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AlphaLens | Premium Market Analytics")
        self.geometry("1400x950")
        self.configure(fg_color=BG_COLOR)
        
        self.grid_rowconfigure(2, weight=1) 
        self.grid_columnconfigure(0, weight=1)
        
        self._build_market_strip()
        self._build_navbar()
        
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)
        
        self.dashboard_view   = DashboardView(self.content_container, self)
        self.news_view        = NewsView(self.content_container)
        self.insights_view    = InsightsView(self.content_container)
        self.watchlist_view   = WatchlistView(self.content_container)
        self.how_it_works_view = HowItWorksView(self.content_container)
        self.about_view       = AboutView(self.content_container)
        
        self.views = {
            "Dashboard":    self.dashboard_view,
            "Insights":     self.insights_view,
            "Watchlist":    self.watchlist_view,
            "News":         self.news_view,
            "How It Works": self.how_it_works_view,
            "About":        self.about_view
        }
        
        # Initialize Loading Overlay globally
        self.overlay = LoadingOverlay(self.content_container)
        
        self.show_view("Dashboard")

    def show_insight_toast(self, ticker):
        """Show the slide-in corner toast prompting user to visit Insights tab."""
        if hasattr(self, '_toast'):
            try: self._toast.dismiss()
            except: pass
        n = getattr(self.insights_view, 'last_insight_count', 8)
        self._toast = InsightToast(self, ticker, n, lambda: self.show_view("Insights"))

    def _build_market_strip(self):
        self.strip_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0, height=35)
        self.strip_frame.grid(row=0, column=0, sticky="ew")
        self.strip_frame.pack_propagate(False)
        self.strip_lbl = ctk.CTkLabel(self.strip_frame, text="Loading Live Markets...", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED)
        self.strip_lbl.pack(side="left", padx=20, pady=5)
        threading.Thread(target=self._fetch_strip_data).start()

    def _fetch_strip_data(self):
        results = DataEngine.fetch_market_strip()
        if results:
            text_parts = []
            for sym, (price, change) in results.items():
                icon = "▲" if change >= 0 else "▼"
                color_hex = ACCENT_GREEN if change >= 0 else ACCENT_RED
                text_parts.append(f"{sym}: ${price:,.2f} ({icon}{abs(change):.2f}%)")
            final_text = "   |   ".join(text_parts)
            self.after(0, lambda: self.strip_lbl.configure(text=final_text, text_color=TEXT_LIGHT))
        else:
            self.after(0, lambda: self.strip_lbl.configure(text="Market Strip Unavailable"))

    def _build_navbar(self):
        nav_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=70, border_width=1, border_color=BORDER_COLOR)
        nav_frame.grid(row=1, column=0, sticky="ew")
        nav_frame.pack_propagate(False)
        
        brand_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        brand_frame.pack(side="left", padx=30, pady=15)
        ctk.CTkLabel(brand_frame, text="🔮", font=ctk.CTkFont(size=24)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(brand_frame, text="AlphaLens", font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"), text_color=ACCENT_PURPLE).pack(side="left")
        
        nav_btns_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        nav_btns_frame.pack(side="right", padx=30, pady=15)
        
        self.nav_buttons = {}
        for text in ["Dashboard", "Insights", "Watchlist", "News", "How It Works", "About"]:
            btn = ctk.CTkButton(
                nav_btns_frame, text=text, width=100, height=35,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                fg_color="transparent", text_color=TEXT_MUTED, hover_color=CARD_BG,
                command=lambda t=text: self.show_view(t)
            )
            btn.pack(side="left", padx=5)
            self.nav_buttons[text] = btn

    def show_view(self, view_name):
        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color=CARD_BG, text_color=ACCENT_PURPLE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)
        for view in self.views.values():
            view.grid_remove()
            
        self.views[view_name].grid(row=0, column=0, sticky="nsew")
        self.views[view_name].tkraise()
# main function
if __name__ == "__main__":
    app = AlphaLensApp()
    app.mainloop()
