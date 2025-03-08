document.getElementById('analyzeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitButton = this.querySelector('button[type="submit"]');
    
    // Adiciona as premissas ao formData
    formData.append('growth_rate', document.getElementById('growth_rate').value);
    formData.append('discount_rate', document.getElementById('discount_rate').value);
    formData.append('projection_years', document.getElementById('projection_years').value);
    formData.append('perpetual_growth', document.getElementById('perpetual_growth').value);
    
    // Desabilita o botão e mostra loading
    submitButton.disabled = true;
    submitButton.innerHTML = 'Analisando...';
    
    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Atualiza dados fundamentalistas
            document.getElementById('nome').textContent = data.fundamentals.nome;
            document.getElementById('setor').textContent = data.fundamentals.setor;
            document.getElementById('preco_atual').textContent = data.fundamentals.preco_atual.toFixed(2);
            document.getElementById('pl').textContent = data.fundamentals.pl.toFixed(2);
            document.getElementById('pvp').textContent = data.fundamentals.pvp.toFixed(2);
            document.getElementById('dividend_yield').textContent = data.fundamentals.dividend_yield.toFixed(2);
            document.getElementById('roic').textContent = data.fundamentals.roic.toFixed(2);
            document.getElementById('roe').textContent = data.fundamentals.roe.toFixed(2);
            document.getElementById('margem_liquida').textContent = data.fundamentals.margem_liquida.toFixed(2);
            
            // Atualiza valuation
            document.getElementById('dcf_value').textContent = 
                data.valuation.dcf ? `R$ ${data.valuation.dcf.toFixed(2)}` : 'N/A';
            
            const multiples_avg = (data.valuation.multiples.pe_valuation + data.valuation.multiples.pb_valuation) / 2;
            document.getElementById('multiples_value').textContent = 
                multiples_avg ? `R$ ${multiples_avg.toFixed(2)}` : 'N/A';
            
            document.getElementById('asset_value').textContent = 
                data.valuation.asset_based ? `R$ ${data.valuation.asset_based.toFixed(2)}` : 'N/A';
            
            // Atualiza premissas
            document.getElementById('dcf_growth').textContent = data.valuation.premissas.dcf.growth_rate.toFixed(1);
            document.getElementById('dcf_discount').textContent = data.valuation.premissas.dcf.discount_rate.toFixed(1);
            document.getElementById('dcf_years').textContent = data.valuation.premissas.dcf.projection_years;
            document.getElementById('dcf_terminal').textContent = data.valuation.premissas.dcf.perpetual_growth.toFixed(1);
            document.getElementById('mult_pe').textContent = data.valuation.premissas.multiples.sector_pe.toFixed(1);
            document.getElementById('mult_pb').textContent = data.valuation.premissas.multiples.sector_pb.toFixed(1);
            
            // Cria o gráfico de candlestick com tema escuro
            const trace = {
                x: data.chart_data.dates,
                close: data.chart_data.prices,
                high: data.chart_data.high,
                low: data.chart_data.low,
                open: data.chart_data.open,
                
                increasing: {line: {color: '#00C805'}},
                decreasing: {line: {color: '#FF3319'}},
                
                type: 'candlestick',
                xaxis: 'x',
                yaxis: 'y'
            };

            const layout = {
                title: {
                    text: `Histórico de Preços - ${formData.get('ticker').toUpperCase()}`,
                    font: {
                        color: '#ffffff'
                    }
                },
                paper_bgcolor: '#2d2d2d',
                plot_bgcolor: '#2d2d2d',
                yaxis: {
                    title: 'Preço (R$)',
                    tickformat: '.2f',
                    gridcolor: '#3d3d3d',
                    zerolinecolor: '#3d3d3d',
                    tickfont: {
                        color: '#ffffff'
                    }
                },
                xaxis: {
                    title: 'Data',
                    gridcolor: '#3d3d3d',
                    zerolinecolor: '#3d3d3d',
                    tickfont: {
                        color: '#ffffff'
                    }
                },
                height: 600,
                width: null,
                autosize: true,
                margin: {
                    l: 50,
                    r: 50,
                    t: 50,
                    b: 50
                }
            };

            Plotly.newPlot('priceChart', [trace], layout);
            
            // Mostra os resultados
            document.getElementById('results').style.display = 'block';
        } else {
            alert('Erro ao analisar ação: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Ocorreu um erro ao processar a análise.');
    })
    .finally(() => {
        // Reabilita o botão
        submitButton.disabled = false;
        submitButton.innerHTML = 'Analisar';
    });
});

// Adiciona um listener para redimensionar o gráfico quando a janela for redimensionada
window.addEventListener('resize', function() {
    Plotly.Plots.resize('priceChart');
});