# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def get_stock_data(ticker):
    """Busca dados da ação usando yfinance"""
    if not ticker.endswith('.SA'):
        ticker = f"{ticker}.SA"
    
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Correção do Dividend Yield
    if 'dividendYield' in info and info['dividendYield']:
        info['dividendYield'] = info['dividendYield'] * 100
    else:
        info['dividendYield'] = 0
    
    # Correção do ROIC
    if 'returnOnCapital' not in info or not info['returnOnCapital']:
        # Cálculo manual do ROIC
        ebit = info.get('ebit', 0)
        total_assets = info.get('totalAssets', 0)
        current_liab = info.get('totalCurrentLiabilities', 0)
        if total_assets > 0 and current_liab > 0:
            invested_capital = total_assets - current_liab
            info['returnOnCapital'] = (ebit / invested_capital) * 100 if invested_capital > 0 else 0
    
    hist = stock.history(period="5y")
    return info, hist

def calculate_dcf(info, hist, premissas):
    """Calcula o valor estimado usando Discounted Cash Flow com premissas customizadas"""
    try:
        # Pega o último Free Cash Flow disponível
        fcf = info.get('freeCashflow', 0)
        
        if fcf <= 0:
            return None
        
        # Usa as premissas fornecidas
        growth_rate = premissas['growth_rate'] / 100
        discount_rate = premissas['discount_rate'] / 100
        years = premissas['projection_years']
        terminal_growth = premissas['perpetual_growth'] / 100
        
        # Cálculo do DCF
        future_fcf = []
        for i in range(years):
            fcf *= (1 + growth_rate)
            future_fcf.append(fcf)
        
        terminal_value = future_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        
        present_value = 0
        for i, fc in enumerate(future_fcf):
            present_value += fc / ((1 + discount_rate) ** (i + 1))
        
        present_value += terminal_value / ((1 + discount_rate) ** years)
        
        shares_outstanding = info.get('sharesOutstanding', 0)
        if shares_outstanding > 0:
            return round(present_value / shares_outstanding, 2)
        return None
    except Exception as e:
        print(f"Erro no cálculo DCF: {e}")
        return None

def calculate_multiples(info):
    """Calcula valoração por múltiplos"""
    try:
        # Premissas - médias do setor
        sector_pe = 15  # P/L médio do setor
        sector_pb = 2   # P/VP médio do setor
        
        # Armazena as premissas para exibição
        global multiples_premissas
        multiples_premissas = {
            'sector_pe': sector_pe,
            'sector_pb': sector_pb
        }
        
        earnings_per_share = info.get('trailingEps', 0)
        book_value_per_share = info.get('bookValue', 0)
        
        pe_valuation = round(earnings_per_share * sector_pe, 2) if earnings_per_share > 0 else None
        pb_valuation = round(book_value_per_share * sector_pb, 2) if book_value_per_share > 0 else None
        
        return {
            'pe_valuation': pe_valuation,
            'pb_valuation': pb_valuation
        }
    except Exception as e:
        print(f"Erro no cálculo por múltiplos: {e}")
        return {
            'pe_valuation': None,
            'pb_valuation': None
        }

def calculate_asset_based(info):
    """Calcula valoração baseada em patrimônio líquido por ação"""
    try:
        # Busca o valor do patrimônio líquido e quantidade de ações
        stockholders_equity = info.get('totalStockholderEquity', 0)
        shares_outstanding = info.get('sharesOutstanding', 0)
        
        if shares_outstanding > 0 and stockholders_equity > 0:
            valor_por_acao = stockholders_equity / shares_outstanding
            return round(valor_por_acao, 2)
        return None
    except Exception as e:
        print(f"Erro no cálculo patrimonial: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form['ticker'].upper()
    
    # Recebe as premissas do formulário
    premissas = {
        'growth_rate': float(request.form.get('growth_rate', 10)),
        'discount_rate': float(request.form.get('discount_rate', 12)),
        'projection_years': int(request.form.get('projection_years', 10)),
        'perpetual_growth': float(request.form.get('perpetual_growth', 3))
    }
    
    try:
        info, hist = get_stock_data(ticker)
        
        # Cálculos de valuation com as premissas customizadas
        dcf_value = calculate_dcf(info, hist, premissas)
        multiples = calculate_multiples(info)
        asset_value = calculate_asset_based(info)
        
        # Prepara dados do gráfico
        chart_data = {
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'prices': hist['Close'].tolist(),
            'high': hist['High'].tolist(),
            'low': hist['Low'].tolist(),
            'open': hist['Open'].tolist()
        }
        
        return jsonify({
            'success': True,
            'fundamentals': {
                'nome': info.get('longName', ''),
                'setor': info.get('sector', ''),
                'preco_atual': info.get('currentPrice', 0),
                'pl': info.get('trailingPE', 0),
                'pvp': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'roic': info.get('returnOnCapital', 0),
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'margem_liquida': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0
            },
            'valuation': {
                'dcf': dcf_value,
                'multiples': multiples,
                'asset_based': asset_value,
                'premissas': {
                    'dcf': premissas,
                    'multiples': multiples_premissas
                }
            },
            'chart_data': chart_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)