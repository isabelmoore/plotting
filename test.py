import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

def df_to_html_plots(df, time_col='time', output_file='report.html'):
    """
    Export DataFrame to a tall, vertically-stacked HTML report.
    Unrolls arrays into time-series plots with specific unit labels.
    """
    times = df[time_col].tolist()
    
    # Mapping: (start_index, end_index, Label, Unit)
    ARRAY_MAPPINGS = {
        'x_own': [
            (0, 3, "ECI Position", "m"),
            (3, 6, "ECI Velocity", "m/s"),
            (6, 7, "Mass", "kg"),
            (7, 11, "Orientation Quaternion", "unitless"),
            (11, 14, "Angular Velocity", "rad/s")
        ]
    }

    plot_blocks = []
    toc_links = []
    first_plot = True

    def apply_tall_layout(fig, title_text, unit_text):
        fig.update_layout(
            title=f"<b>{title_text}</b>",
            xaxis_title="Time",
            yaxis_title=f"Value ({unit_text})" if unit_text else "Value",
            height=600, 
            template="plotly_white",
            margin=dict(l=60, r=40, t=80, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            dragmode="zoom"
        )

    def create_trace(x, y, name):
        return go.Scatter(x=x, y=y, name=name, mode='lines+markers', line=dict(width=2))

    for col in df.columns:
        if col == time_col:
            continue
        
        first_val = df[col].iloc[0]
        is_array = isinstance(first_val, (list, np.ndarray)) and len(np.array(first_val).flatten()) > 1

        if not is_array:
            fig = go.Figure(create_trace(times, df[col].tolist(), col))
            apply_tall_layout(fig, f"Scalar: {col}", None)
            plot_id = f"plot_{col}"
            toc_links.append(f'<li><a href="#{plot_id}">{col}</a></li>')
            plot_blocks.append((plot_id, pio.to_html(fig, full_html=False, include_plotlyjs=first_plot, div_id=plot_id+"_fig")))
            first_plot = False

        elif col.lower() in ARRAY_MAPPINGS:
            data_matrix = np.array(df[col].tolist())
            for start, end, label, unit in ARRAY_MAPPINGS[col.lower()]:
                fig = go.Figure()
                for i in range(start, end):
                    suffix = ["_X", "_Y", "_Z", "_W"][i-start] if (end-start) <= 4 else f"_{i}"
                    fig.add_trace(create_trace(times, data_matrix[:, i], f"{label}{suffix}"))
                
                apply_tall_layout(fig, f"{col.upper()}: {label}", unit)
                if "Quaternion" in label:
                    fig.update_layout(yaxis_range=[-1.1, 1.1])

                plot_id = f"plot_{col}_{start}"
                toc_links.append(f'<li><a href="#{plot_id}">{col.upper()}: {label}</a></li>')
                plot_blocks.append((plot_id, pio.to_html(fig, full_html=False, include_plotlyjs=first_plot, div_id=plot_id+"_fig")))
                first_plot = False

        else:
            data_matrix = np.array(df[col].tolist())
            fig = go.Figure()
            for i in range(data_matrix.shape[1]):
                fig.add_trace(create_trace(times, data_matrix[:, i], f"{col}[{i}]"))
            
            apply_tall_layout(fig, f"Array: {col}", "units")
            plot_id = f"plot_{col}"
            toc_links.append(f'<li><a href="#{plot_id}">{col}</a></li>')
            plot_blocks.append((plot_id, pio.to_html(fig, full_html=False, include_plotlyjs=first_plot, div_id=plot_id+"_fig")))
            first_plot = False

    # Note: Double {{ }} are ONLY needed here because this is an f-string
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mission Telemetry Report</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; display: flex; margin: 0; background: #f4f7f9; }}
            #sidebar {{ width: 300px; background: #2c3e50; color: white; height: 100vh; overflow-y: auto; position: fixed; padding: 20px; box-sizing: border-box; }}
            #main {{ margin-left: 300px; padding: 40px; width: calc(100% - 300px); }}
            #sidebar h2 {{ font-size: 1.2em; border-bottom: 1px solid #555; padding-bottom: 10px; }}
            #sidebar ul {{ list-style: none; padding: 0; }}
            #sidebar a {{ color: #bdc3c7; text-decoration: none; font-size: 0.85em; display: block; padding: 8px 0; border-bottom: 1px solid #3e4f5f; }}
            #sidebar a:hover {{ color: white; background: #34495e; padding-left: 5px; transition: 0.2s; }}
            .plot-card {{ background: white; padding: 20px; margin-bottom: 50px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); scroll-margin-top: 20px; }}
            h1 {{ color: #2c3e50; margin-top: 0; }}
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h2>Telemetry Index</h2>
            <ul>{''.join(toc_links)}</ul>
        </div>
        <div id="main">
            <h1>Mission Data Report</h1>
            {''.join([f'<div id="{pid}" class="plot-card">{phtml}</div>' for pid, phtml in plot_blocks])}
        </div>

        <script>
            window.onload = function() {{
                var plots = document.querySelectorAll('.js-plotly-plot');
                for (var i = 0; i < plots.length; i++) {{
                    plots[i].on('plotly_relayout', function(eventdata) {{
                        if (eventdata['xaxis.range[0]'] || eventdata['xaxis.autorange']) {{
                            var update = {{
                                'xaxis.range[0]': eventdata['xaxis.range[0]'],
                                'xaxis.range[1]': eventdata['xaxis.range[1]'],
                                'xaxis.autorange': eventdata['xaxis.autorange']
                            }};
                            plots.forEach(function(p) {{
                                if (p !== event.target) {{ Plotly.relayout(p, update); }}
                            }});
                        }}
                    }});
                }}
            }};
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    print(f"Report generated: {output_file}")

if __name__ == "__main__":
    # Fixed test data: Normal single braces here!
    test_data = {
        'time': np.linspace(0, 10, 50),
        'x_own': [np.random.randn(14) for _ in range(50)],
        'battery_voltage': np.random.uniform(11, 12.6, 50)
    }
    df = pd.DataFrame(test_data)
    df_to_html_plots(df, output_file='telemetry_report.html')
