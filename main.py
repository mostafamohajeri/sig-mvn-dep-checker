import jgrapht

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


def list_external_dependencies(g, v_attrs):
    g_dep = jgrapht.create_graph(directed=True, weighted=False,
                                 allowing_self_loops=True, allowing_multiple_edges=False, any_hashable=True)
    for e in g.edges:
        if not (v_attrs[g.edge_target(e)]['product'] == v_attrs[g.edge_source(e)]['product']):
            g_dep.add_vertex(v_attrs[g.edge_source(e)]['product'])
            g_dep.add_vertex(v_attrs[g.edge_target(e)]['product'])
            g.add_edge(v_attrs[g.edge_source(e)]['product'],
                       v_attrs[g.edge_target(e)]['product'])

    return g_dep


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

    ext_depend_graph = list_external_dependencies(g, v_attrs)


if __name__ == "__main__":
    main()
