import jgrapht
import jgrapht.drawing.draw_matplotlib as drawing

import matplotlib.pyplot as plt

filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-docker-2.12.1-reduced.json"
# filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-cassandra-2.12.1-merged.json"
v_attrs = {}


def import_id_cb(vertex):
    """ Set node id to original JSON value """
    return int(vertex)


def vertex_attribute_cb(vertex, attribute_name, attribute_value):
    """Callback function for vertex attributes
        Adds the attributes to v_attrs dict, with node id as key."""
    if vertex not in v_attrs:
        v_attrs[vertex] = {}

    if attribute_name == 'application_node':
        v_attrs[vertex][attribute_name] = (attribute_value == 'true')
    else:
        v_attrs[vertex][attribute_name] = attribute_value


def list_external_dependencies_application(g, v_attrs):
    """List the edges from an application_node to a non application_node"""
    ext_depend = []
    for v in g.vertices:
        if v_attrs[v]['application_node']:
            for e in g.outedges_of(v):
                if not v_attrs[g.edge_target(e)]['application_node']:
                    ext_depend.append(g.edge_target(e))

    return ext_depend


def draw_external_dependencies(g, v_attrs):
    """ Use matplolib to plot a dependency graph between attributes """
    attr = 'product'
    mapping = []
    g_dep = jgrapht.create_graph(directed=True, weighted=False,
                                 allowing_self_loops=True, allowing_multiple_edges=True, any_hashable=False)
    for e in g.edges:
        if not (v_attrs[g.edge_target(e)][attr] == v_attrs[g.edge_source(e)][attr]):
            src = v_attrs[g.edge_source(e)][attr]
            dst = v_attrs[g.edge_target(e)][attr]

            if src not in mapping:
                mapping.append(src)
                src = mapping.index(src)
                g_dep.add_vertex(src)
            else:
                src = mapping.index(src)

            if dst not in mapping:
                mapping.append(dst)
                dst = mapping.index(dst)
                g_dep.add_vertex(dst)
            else:
                dst = mapping.index(dst)

            # Add edge if not in graph 
            if not g_dep.contains_edge_between(src, dst):
                g_dep.add_edge(src, dst)

    # drawing.draw_jgrapht(g_dep, positions=drawing.layout(g_dep, name="random"))
    # plt.show()
    positions = drawing.layout(g_dep, seed=10, name="circular")
    drawing.draw_jgrapht(
        g_dep,
        positions=positions,
        node_label=True,
        node_color=range(len(g.vertices)),
        node_cmap=plt.cm.Blues,
        edge_linewidth=4,
        arrow=True,
        arrow_color="orange",
        arrow_line="dotted",
        connection_style="arc3,rad=-0.3",
        axis=False,
    )

    vertex_names = {}
    for i in range(len(mapping)):
        vertex_names[i] = mapping[i]

    # Draw the edge labels with custom edge names
    # Draw the vertex labels with custom vertex names
    drawing.draw_jgrapht_vertex_labels(
        g_dep,
        positions=positions,
        labels=vertex_names,
    )
    plt.show()


def main():
    g = jgrapht.create_graph(directed=True, weighted=False,
                             allowing_self_loops=True, allowing_multiple_edges=False, any_hashable=False)
    jgrapht.io.importers.read_json(g, filename,
                                   import_id_cb=import_id_cb,
                                   vertex_attribute_cb=vertex_attribute_cb)

    # ext_depend = list_external_dependencies_application(g, v_attrs)
    # print(len(ext_depend))
    # print(ext_depend)
    # print([v_attrs[v]['product'] for v in ext_depend])
    # print(len(set([v_attrs[v]['product'] for v in ext_depend])))

    ext_depend_graph = draw_external_dependencies(g, v_attrs)

if __name__ == "__main__":
    main()
