import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px

# Load dictionary
def load_dictionary(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

dictionary = load_dictionary("words.txt")

# Spell-check function
def wagner_fischer(s1, s2):
    len_s1, len_s2 = len(s1), len(s2)
    if len_s1 > len_s2:
        s1, s2 = s2, s1
        len_s1, len_s2 = len_s2, len_s1

    current_row = range(len_s1 + 1)
    for i in range(1, len_s2 + 1):
        previous_row, current_row = current_row, [i] + [0] * len_s1
        for j in range(1, len_s1 + 1):
            add, delete, change = previous_row[j] + 1, current_row[j-1] + 1, previous_row[j-1]
            if s1[j-1] != s2[i-1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[len_s1]

def spell_check(word, dictionary):
    suggestions = []

    for correct_word in dictionary:
        distance = wagner_fischer(word, correct_word)
        suggestions.append((correct_word, distance))

    return suggestions


app = dash.Dash(__name__)


# Layout of the app
app.layout = html.Div([
    # Landing page
    html.Div([
        html.H1("Welcome to Spell Checker App"),
        html.Button("Start Spell Checking", id="start-button"),
    ], id="landing-page"),

    
    html.Div([
        # Input 
        html.Div([
            html.Label('Enter a word:'),
            dcc.Input(id='input-word', type='text', value='wrlod'),
        ], className="module"),

        # Threshold
        html.Div([
            html.Label('Set Edit Distance Threshold:'),
            dcc.Slider(
                id='threshold-slider',
                min=0,
                max=10,
                step=1,
                marks={i: str(i) for i in range(11)},
                value=3
            ),
        ], className="module"),

        # Button 
        html.Div([
            html.Button('Check Spelling', id='check-button', n_clicks=0),
        ], className="module"),

        # Chart 
        html.Div([
            dcc.Graph(id='edit-distance-chart'),
        ], className="module"),
    ], id="spell-check-page", style={'display': 'none'}),
])

# Callback to switch between landing page and spell-checking page
@app.callback(
    Output('landing-page', 'style'),
    Output('spell-check-page', 'style'),
    Input('start-button', 'n_clicks')
)
def switch_page(n_clicks):
    if n_clicks:
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'block'}, {'display': 'none'}

# Callback to update chart
@app.callback(
    Output('edit-distance-chart', 'figure'),
    [Input('check-button', 'n_clicks')],
    [State('input-word', 'value'),
     State('threshold-slider', 'value')]
)
def update_chart(n_clicks, input_word, threshold):
    # Perform spell check
    suggestions = spell_check(input_word, dictionary)
    
    # Create a DataFrame from suggestions
    df = pd.DataFrame(suggestions, columns=['Word', 'Edit Distance'])
    
    # Filter words above the threshold
    df_above_threshold = df[df['Edit Distance'] <= threshold]

    # Select top 10 suggestions
    df_top_10 = df_above_threshold.nsmallest(10, 'Edit Distance')

    # Plotly Express bar chart
    fig = px.bar(
        df_top_10,
        x='Word',
        y='Edit Distance',
        color='Edit Distance',
        labels={'Word': 'Words', 'Edit Distance': 'Edit Distance'},
        title=f'Top 10 Suggestions for {input_word} (Threshold: {threshold})',
        width=800,
        height=400
    )

    # Update layout for better readability
    fig.update_xaxes(tickangle=45, tickmode='array', tickvals=df_top_10.index, showgrid=False)

    # Add interactive hover information
    fig.update_traces(hovertemplate='Word: %{x}<br>Edit Distance: %{y}')

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
