import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio


def df_to_html_plots(df, time_col='time', output_file='report.html'):
    """
    Export DataFrame to HTML with interactive plots.
    
    - Scalar columns: plotted as time series (value vs time)
    - Array columns: each gets its own plot with index as x-axis, values as y-axis, time slider
    """
    times = df[time_col].tolist()
    
    # Detect scalar vs array columns
    scalar_cols = []
    array_cols = []
    
    for col in df.columns:
        if col == time_col:
            continue
        
        first_val = df[col].iloc[0]
        
        # Check if it's an array/list with length > 1
        if isinstance(first_val, (list, np.ndarray)) and len(np.array(first_val).flatten()) > 1:
            array_cols.append(col)
        else:
            scalar_cols.append(col)
    
    print(f"Scalar columns (plot vs time): {scalar_cols}")
    print(f"Array columns (slider for time): {array_cols}")
    
    all_figs = []
    
    # --- Scalar columns: value vs time ---
    for col in scalar_cols:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times, 
            y=df[col].tolist(), 
            mode='lines+markers',
            line=dict(width=2),
            marker=dict(size=6)
        ))
        fig.update_layout(
            title=col,
            xaxis_title='Time',
            yaxis_title=col,
            height=300
        )
        all_figs.append(('scalar', col, fig))
    
    # --- Array columns: index as x, values as y, time slider ---
    for col in array_cols:
        all_data = [np.array(df[col].iloc[t]).flatten().tolist() for t in range(len(times))]
        x_vals = list(range(len(all_data[0])))
        
        # Calculate y range across all time steps
        all_vals = np.concatenate([np.array(arr) for arr in all_data])
        y_min, y_max = float(all_vals.min()), float(all_vals.max())
        padding = 0.1 * (y_max - y_min) if y_max != y_min else 1
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals, 
            y=all_data[0], 
            mode='lines+markers',
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        # Create frames for each time step
        frames = [go.Frame(data=[go.Scatter(x=x_vals, y=all_data[i])], name=str(i)) 
                  for i in range(len(times))]
        fig.frames = frames
        
        # Create slider steps
        steps = [dict(
            args=[[str(i)], dict(frame=dict(duration=0, redraw=True), mode='immediate')],
            label=f"{times[i]:.2f}" if isinstance(times[i], float) else str(times[i]), 
            method='animate'
        ) for i in range(len(times))]
        
        fig.update_layout(
            title=col,
            xaxis_title='Index',
            yaxis_title='Value',
            yaxis_range=[y_min - padding, y_max + padding],
            height=400,
            updatemenus=[dict(
                type='buttons', showactive=False, y=-0.15, x=0.1,
                buttons=[
                    dict(label='▶ Play', method='animate',
                         args=[None, dict(frame=dict(duration=300, redraw=True), fromcurrent=True)]),
                    dict(label='⏸ Pause', method='animate',
                         args=[[None], dict(frame=dict(duration=0), mode='immediate')])
                ]
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(prefix='Time: ', visible=True),
                pad=dict(t=50),
                len=0.8,
                x=0.1,
                y=-0.05,
                steps=steps
            )]
        )
        all_figs.append(('array', col, fig))
    
    # Build HTML
    html = '''<!DOCTYPE html>
<html><head><title>Data Report</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; background: #fafafa; }
h1 { text-align: center; }
h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-top: 40px; }
.plot-container { background: white; border-radius: 8px; padding: 15px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
</head><body>
<h1>Data Report</h1>
'''
    
    first_plot = True
    
    # Add scalar plots (value vs time)
    scalar_figs = [f for f in all_figs if f[0] == 'scalar']
    if scalar_figs:
        html += '<h2>Scalar Values Over Time</h2>\n'
        for typ, col, fig in scalar_figs:
            include_js = first_plot
            first_plot = False
            html += f'<div class="plot-container">\n{pio.to_html(fig, full_html=False, include_plotlyjs=include_js)}\n</div>\n'
    
    # Add array plots (with time slider)
    array_figs = [f for f in all_figs if f[0] == 'array']
    if array_figs:
        html += '<h2>Array Data (Use Time Slider)</h2>\n'
        for typ, col, fig in array_figs:
            include_js = first_plot
            first_plot = False
            html += f'<div class="plot-container">\n{pio.to_html(fig, full_html=False, include_plotlyjs=include_js)}\n</div>\n'
    
    html += '</body></html>'
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Saved to {output_file}")


# =========================
# TEST
# =========================
if __name__ == "__main__":
    
    # Test data with BOTH scalar and array columns
    test = {
        'time': [0, 1, 2],
        'x_own': [[1, 2, 3], [2, 3, 4], [3, 4, 5]],  # array - gets time slider
        'y_own': [[5, 6, 7], [6, 7, 8], [7, 8, 9]],  # array - gets time slider
        'z': [1, 2, 3],                               # scalar - plotted vs time
        'error': [0.5, 0.3, 0.1]                      # scalar - plotted vs time
    }
    
    df = pd.DataFrame(test)
    
    print("DataFrame:")
    print(df)
    print()
    
    df_to_html_plots(df, time_col='time', output_file='test_output.html')
