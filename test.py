import pandas as pd
import numpy as np


def df_to_html_plots(df, time_col='time', output_file='report.html'):
    """
    Export DataFrame to HTML with interactive plots.
    
    - Single value columns: plotted as time series (value vs time)
    - Nested array columns: each gets its own plot with a time slider
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a time column and mixed data types
    time_col : str
        Name of the time column
    output_file : str
        Output HTML file path
    """
    times = df[time_col].tolist()
    
    # Separate columns by type
    single_value_cols = []
    nested_array_cols = []
    
    for col in df.columns:
        if col == time_col:
            continue
        first_val = df[col].iloc[0]
        if isinstance(first_val, (list, np.ndarray)) and len(first_val) > 1:
            nested_array_cols.append(col)
        else:
            single_value_cols.append(col)
    
    # Build HTML
    html_parts = ['''
<!DOCTYPE html>
<html>
<head>
    <title>Data Report</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #fafafa; }
        h1 { text-align: center; color: #333; }
        h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-top: 40px; }
        .plot-container { background: white; border-radius: 8px; padding: 15px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <h1>Data Report</h1>
''']
    
    # --- Single value time series ---
    if single_value_cols:
        html_parts.append('<h2>Metrics Over Time</h2>')
        for col in single_value_cols:
            values = df[col].tolist()
            div_id = f"plot_{col.replace(' ', '_').replace('(', '').replace(')', '')}"
            html_parts.append(f'''
    <div class="plot-container">
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', [{{
                x: {times},
                y: {values},
                mode: 'lines+markers',
                line: {{width: 2}},
                marker: {{size: 5}}
            }}], {{
                title: '{col}',
                xaxis: {{title: 'Time'}},
                yaxis: {{title: '{col}'}},
                height: 300,
                margin: {{t: 50, b: 50, l: 60, r: 30}}
            }});
        </script>
    </div>
''')
    
    # --- Nested arrays with individual sliders ---
    if nested_array_cols:
        html_parts.append('<h2>Array Data (Use Sliders)</h2>')
        for col in nested_array_cols:
            div_id = f"plot_{col.replace(' ', '_').replace('(', '').replace(')', '')}"
            
            # Prepare data
            all_data = [np.array(df[col].iloc[t]).tolist() for t in range(len(times))]
            x_vals = list(range(len(all_data[0])))
            
            # Y-axis range
            all_vals = np.concatenate([np.array(arr) for arr in df[col]])
            y_min, y_max = float(all_vals.min()), float(all_vals.max())
            padding = 0.1 * (y_max - y_min) if y_max != y_min else 1
            y_range = [y_min - padding, y_max + padding]
            
            # Frames and steps
            frames_json = [{'name': str(i), 'data': [{'x': x_vals, 'y': all_data[i]}]} for i in range(len(times))]
            steps_json = [{'args': [[str(i)], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}], 'label': f"{times[i]:.2f}", 'method': 'animate'} for i in range(len(times))]
            
            html_parts.append(f'''
    <div class="plot-container">
        <div id="{div_id}"></div>
        <script>
            (function() {{
                Plotly.newPlot('{div_id}', [{{
                    x: {x_vals},
                    y: {all_data[0]},
                    mode: 'lines+markers',
                    line: {{width: 2}},
                    marker: {{size: 6}}
                }}], {{
                    title: '{col}',
                    xaxis: {{title: 'Index'}},
                    yaxis: {{title: 'Value', range: {y_range}}},
                    height: 350,
                    margin: {{t: 50, b: 100, l: 60, r: 30}},
                    updatemenus: [{{
                        type: 'buttons',
                        showactive: false,
                        y: -0.15,
                        x: 0.05,
                        buttons: [
                            {{label: '▶ Play', method: 'animate', args: [null, {{frame: {{duration: 150, redraw: true}}, fromcurrent: true}}]}},
                            {{label: '⏸ Pause', method: 'animate', args: [[null], {{frame: {{duration: 0}}, mode: 'immediate'}}]}}
                        ]
                    }}],
                    sliders: [{{
                        active: 0,
                        currentvalue: {{prefix: 'Time: ', visible: true, xanchor: 'center'}},
                        pad: {{b: 10, t: 20}},
                        len: 0.75,
                        x: 0.25,
                        steps: {steps_json}
                    }}]
                }}).then(function() {{
                    Plotly.addFrames('{div_id}', {frames_json});
                }});
            }})();
        </script>
    </div>
''')
    
    html_parts.append('</body></html>')
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(html_parts))
    
    print(f"Saved to {output_file}")