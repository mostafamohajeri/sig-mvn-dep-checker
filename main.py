import jgrapht

filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-iostreams-2.12.1-merged.json"

filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-cassandra-2.12.1-merged.json"
v_attrs = {}


def import_id_cb(vertex):
    """ Set node id to original JSON value """
    return int(vertex)


def vertex_attribute_cb(vertex, attribute_name, attribute_value):
    """Callback function for vertex attributes
        Adds the attributes to v_attrs dict, with node id as key."""
    if vertex not in v_attrs:
        v_attrs[vertex] = {}
    v_attrs[vertex][attribute_name] = attribute_value


def main():
    g = jgrapht.create_graph(directed=True, weighted=False,
                             allowing_self_loops=True, allowing_multiple_edges=False, any_hashable=False)
    jgrapht.io.importers.read_json(g, filename,
                                   import_id_cb=import_id_cb,
                                   vertex_attribute_cb=vertex_attribute_cb)

    for v in g.vertices:
        print('Vertex {}'.format(v))
        edges = g.outedges_of(v)

        print(v_attrs[v]['ID'])

        for e in edges:
            print('Vertex {} edge {}'.format(v, e))


if __name__ == "__main__":
    main()
