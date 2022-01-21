from platform import node
import networkx as nx
import dash
import dash_cytoscape as cyto
import dash_html_components as html
import json

from dash import dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__)

# g = nx.drawing.nx_agraph.read_dot("dot_files/vulnerability.dot")
g = nx.drawing.nx_agraph.read_dot(
    "dot_files/org.apache.logging.log4j.samples.log4j-samples-flume-common-2.12.1-merged.json.dot")


styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

base_stylesheet = [
    {
        "selector": 'node',  # For all nodes
        'style': {
            "opacity": 0.9,
            "label": "data(label)",  # Label of node to display
            "background-color": "#07ABA0",  # node color
            "color": "#008B80"  # node label color
        }
    },
    {
        "selector": 'edge',  # For all edges
        "style": {
            "target-arrow-color": "#C5D3E2",  # Arrow color
            "target-arrow-shape": "triangle",  # Arrow shape
            "line-color": "#C5D3E2",  # edge color
            'arrow-scale': 2,  # Arrow size
            # Default curve-If it is style, the arrow will not be displayed, so specify it
            'curve-style': 'bezier'
        }
    },
    {
        "selector": ".MEDIUM",
        "style": {
            "background-color": "orange"
        }
    },
    {
        "selector": ".HIGH",
        "style": {
            "background-color": "red"
        }
    },
    {
        "selector": "[num_succcessors = 0]",
        "style": {
            'shape': 'square'
        }
    }
]

collapsed_nodes = list(g.successors("0"))

app.layout = html.Div([
    dcc.Store(id="selected_node", data=None),
    dcc.Store(id="nodes_to_show", data=["0"] + list(g.successors("0"))),
    dcc.Input(id="edge_threshold", type="number", value=10),
    cyto.Cytoscape(
        id='cytoscape-layout-4',
        elements=[],
        style={'width': '100%', 'height': '600px'},
        layout={
            'name': 'breadthfirst',
            'roots': '[id = "0"]'
        },
        stylesheet=base_stylesheet
    ),
    html.Div(
        [html.Pre(id='cytoscape-tapNodeData-json', style=styles['pre']),
         html.Button("Expand/Collapse", id='expand-node', n_clicks=0)]
    )

])


def get_successors(g, id, successors):
    for s in g.successors(id):
        successors.append(int(s))
        successors = get_successors(g, s, successors)

    return successors


@app.callback(Output('nodes_to_show', 'data'),
              Input('expand-node', 'n_clicks'),
              State('nodes_to_show', 'data'),
              State('selected_node', 'data'))
def expandNode(n_clicks, nodes_to_show, selected_node):
    print(f"exandNode: {selected_node = }")
    if selected_node == None:
        return nodes_to_show

    # successors = get_successors(g, str(data['id']), [])
    successors = list(g.successors(str(selected_node)))

    # collapse
    if successors[0] in nodes_to_show:
        collapsed_nodes.append(selected_node)
        for succ in get_successors(g, str(selected_node), []):
            if succ in collapsed_nodes:
                collapsed_nodes.remove(succ)
            if str(succ) in nodes_to_show:
                nodes_to_show.remove(str(succ))

    # expand
    else:
        nodes_to_show += successors
        for succ in successors:
            collapsed_nodes.append(succ)

        collapsed_nodes.remove(selected_node)

    return nodes_to_show


@app.callback(Output('cytoscape-tapNodeData-json', 'children'),
              Output('selected_node', 'data'),
              Input('cytoscape-layout-4', 'tapNodeData'))
def displayTapNodeData(data):
    print(f"displayTapNodeData: {data = }")
    if data is None:
        return "", None

    return json.dumps(data, indent=2), data["id"]


@app.callback(Output("cytoscape-layout-4", "stylesheet"),
              Input('cytoscape-layout-4', 'tapNodeData'),
              Input('edge_threshold', 'value'))
def createElements(data, threshold):
    print(f"createElements: {threshold = }")

    if threshold is None:
        threshold = 10

    stylesheet = base_stylesheet + [{
        'selector': f'[count > {threshold}]',
        'style': {
            'width': "4px",
            "line-color": "#909ba6"
        }
    }]

    if data is None:
        return stylesheet

    stylesheet += [{
        # 'selector': f'[label = \"{data["label"]}\"]',
        'selector': f'[id = \"{data["id"]}\"]',
        'style': {
            "height": "50px",
            "width": "50px"
        }
    }]

    return stylesheet


def get_vul_collapsed(id, data):
    succesors = [id] + [str(x) for x in get_successors(g, id, [])]

    vul = []

    for s in succesors:
        v = json.loads(g.nodes(data=True)[
                       s]["vulnerabilities"].replace("\'", "\""))
        for k in v:
            vul.append(v[k]['severity'])

    return vul


def get_risk(id, data):
    if id in collapsed_nodes:
        vul = get_vul_collapsed(id, data)
    else:
        vul = []
        v = json.loads(data["vulnerabilities"].replace("\'", "\""))
        for k in v:
            vul.append(v[k]['severity'])

    risk = ""
    if "MEDIUM" in vul:
        risk = "MEDIUM"
    if "HIGH" in vul:
        risk = "HIGH"

    return risk


@app.callback(Output('cytoscape-layout-4', 'elements'),
              Input('nodes_to_show', 'data'))
def createElements(nodes_to_show):
    print(f"createElements: {nodes_to_show =}")
    nodes = []

    for (id, data) in g.nodes(data=True):
        if id in nodes_to_show:

            risk = get_risk(id, data)

            nodes.append({
                'data': {'id': id, 'label': data['label'], "num_succcessors": len(list(g.successors(id))), "vulnerabilities": data["vulnerabilities"]},
                'classes': risk
            })
    edges = []

    for src, dst, data in g.edges(data=True):
        if (src in nodes_to_show and dst in nodes_to_show):
            edges.append({'data': {'source': src, 'target': dst,
                                   "count": int(data['count'])}})
    elements = nodes + edges

    return elements


if __name__ == '__main__':
    app.run_server(debug=True)
