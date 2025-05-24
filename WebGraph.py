import dash
from dash import dcc, html, Input, Output
import requests
from bs4 import BeautifulSoup
import networkx as nx
import plotly.graph_objects as go
from urllib.parse import urljoin, urlparse

app = dash.Dash(__name__)


def get_links(url, start=10, end=20):
    """Fetch all unique internal links from the given URL and return a range of links from start to end."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
        links = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(url).netloc:
                links.add(full_url)

        links_list = list(links)
        return links_list[start:end]  # Get the subset
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []


def generate_graph(url, start=10, end=20):
    """Generate a graph with nodes for each internal link found on the page."""
    links = get_links(url, start, end)
    G = nx.DiGraph()
    G.add_node(url)

    for link in links:
        G.add_node(link)
        G.add_edge(url, link)

    return G


def draw_interactive_graph(graph):
    """Draw an interactive Plotly graph from a NetworkX graph."""
    pos = nx.spring_layout(graph, k=0.5)
    for node in graph.nodes():
        graph.nodes[node]['pos'] = pos[node]

    node_x, node_y, node_text = [], [], []
    edge_x, edge_y = [], []

    for edge in graph.edges():
        x0, y0 = graph.nodes[edge[0]]['pos']
        x1, y1 = graph.nodes[edge[1]]['pos']
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1, color='gray'),
        hoverinfo='none'
    )

    for node in graph.nodes():
        x, y = graph.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=dict(
                            text='Interactive Website Link Graph with Clickable Nodes',
                            font=dict(size=16)
                        ),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    return fig


# Initial setup
start_url = "https://www.geeksforgeeks.org"
G = generate_graph(start_url, start=10, end=20)
fig = draw_interactive_graph(G)

app.layout = html.Div([
    html.H1("Interactive Link Graph"),
    dcc.Input(id='url-input', type='text', value=start_url, placeholder="Enter a website URL", style={'width': '60%'}),
    html.Button('Generate Graph', id='generate-graph-btn', n_clicks=0),
    dcc.Graph(id='graph', figure=fig),
    dcc.Store(id='url-store'),
    dcc.Location(id='url-redirect', refresh=True)
])


@app.callback(
    Output('graph', 'figure'),
    Input('generate-graph-btn', 'n_clicks'),
    Input('url-input', 'value')
)
def update_graph(n_clicks, input_url):
    G = generate_graph(input_url, start=30, end=50)  # You can change the range as needed
    fig = draw_interactive_graph(G)
    return fig


@app.callback(
    Output('url-redirect', 'href'),
    Input('graph', 'clickData')
)
def display_click_data(clickData):
    if clickData:
        clicked_url = clickData['points'][0]['text']
        return clicked_url
    return dash.no_update


if __name__ == '__main__':
    app.run(debug=True)
