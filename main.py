from operator import is_
import jgrapht
import jgrapht.drawing.draw_matplotlib as drawing

import matplotlib.pyplot as plt

filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-docker-2.12.1-reduced.json"
# filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-couchdb-2.12.1-merged.json"
# filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-perf-2.12.1-merged.json"
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


def add_node(g, node_name, node_mapping, attributes):
    """" Add a node to g return node id """
    if node_mapping is not None:
        node_mapping.append(node_name)
        node_id = len(node_mapping) - 1
        g.add_vertex(node_id)
    else:
        node_id = g.add_vertex()
    
    attributes[node_id] = {}
    attributes[node_id]['label'] = node_name
    
    return node_id

# def get_node(node_name, node_mapping):
#     """Get node id if node does not excist return None"""
#     if node_name not in node_mapping:
#         node_id = None
#     else:
#         node_id = node_mapping.index(node_name)

#     return node_id

def add_edge(g, src, dst, e_attrs):
    src_node = src
    dst_node = dst

    if src_node is None:
        print("Node {} is not in graph".format(src))
    if dst_node is None:
        print("Node {} is not in graph".format(dst))

    if not g.contains_edge_between(src_node, dst_node):
        edge = g.add_edge(src_node, dst_node)
        e_attrs[edge] = {}
        e_attrs[edge]['count'] = 1


def is_out_target(g, src, dst_name, v_attrs):
    for e in g.outedges_of(src):
        if dst_name == v_attrs[g.edge_target(e)]['label']:
            return True

    return False

def find_out_target(g, src, dst_name, v_attrs):
    for e in g.outedges_of(src):
        if dst_name == v_attrs[g.edge_target(e)]['label']:
            return e
    return False


def add_external_dep_for_attr(g_dep, v_attrs, e_attrs, g, v_attrs_glob, node_id, attr_filter, path):
    # Find direct dependancies of node
    for v in g.vertices:
        if v_attrs_glob[v][attr_filter] == v_attrs[node_id]['label']:
            # add_node(g_dep, v_attrs_glob[v][attr_filter], node_mapping, v_attrs)
            for e in g.outedges_of(v):
                if not (v_attrs_glob[v][attr_filter] == v_attrs_glob[g.edge_target(e)][attr_filter]):
                    if v_attrs_glob[g.edge_target(e)][attr_filter] not in path:

                        edge = find_out_target(g_dep, node_id, v_attrs_glob[g.edge_target(e)][attr_filter], v_attrs)
                        if not edge :
                            target = add_node(g_dep, v_attrs_glob[g.edge_target(e)][attr_filter], None, v_attrs)
                            add_edge(g_dep, node_id, target, e_attrs)
                        else:
                            e_attrs[edge]['count'] += 1

def rec_create_acyclic_dep_tree(g_dep, v_attrs, e_attrs, g, v_attrs_glob, node_id, path, attr_filter):

    path.append(v_attrs[node_id]['label'])

    for e in g_dep.outedges_of(node_id):
        target = g_dep.edge_target(e)
        add_external_dep_for_attr(g_dep, v_attrs, e_attrs, g, v_attrs_glob, target, attr_filter, path)
        rec_create_acyclic_dep_tree(g_dep, v_attrs, e_attrs, g, v_attrs_glob, target, path, attr_filter)

    path.pop()


def create_acyclic_dep_tree(g, v_attrs_glob, attr_filter):
    """ Create an acyclic dependency tree off the components in g with the granularity of attr_filter"""
    v_attrs = {}
    e_attrs = {}
    node_mapping = []
    roots = []

    g_dep = jgrapht.create_graph(directed=True, weighted=False,
                                 allowing_self_loops=False, allowing_multiple_edges=True, any_hashable=False)


    # Find direct dependancies of the appliction
    for v in g.vertices:
        if v_attrs_glob[v]['application_node']:
            if v_attrs_glob[v][attr_filter] not in node_mapping:
                src = add_node(g_dep, v_attrs_glob[v][attr_filter], node_mapping, v_attrs)
            if v_attrs_glob[v][attr_filter] not in roots:
                roots.append(v_attrs_glob[v][attr_filter])
            for e in g.outedges_of(v):
                if not (v_attrs_glob[v][attr_filter] == v_attrs_glob[g.edge_target(e)][attr_filter]):

                    tmp_edge = find_out_target(g_dep, src, v_attrs_glob[g.edge_target(e)][attr_filter], v_attrs)
                    if not tmp_edge:
                        target = add_node(g_dep, v_attrs_glob[g.edge_target(e)][attr_filter], node_mapping, v_attrs)
                        add_edge(g_dep, src, target, e_attrs)
                    else:
                        e_attrs[tmp_edge]['count'] += 1

    # # Go to last layer and check for direct dependancies in there that are not in the path to root
    # print(roots)
    for node in roots:
        rec_create_acyclic_dep_tree(g_dep, v_attrs, e_attrs, g, v_attrs_glob, node_mapping.index(node), [], attr_filter)

    return g_dep, v_attrs, e_attrs


def main():
    g = jgrapht.create_graph(directed=True, weighted=False,
                             allowing_self_loops=True, allowing_multiple_edges=False, any_hashable=False)
    jgrapht.io.importers.read_json(g, filename,
                                   import_id_cb=import_id_cb,
                                   vertex_attribute_cb=vertex_attribute_cb)

    # ext_depend_graph = draw_external_dependencies(g, v_attrs)

    g_dep, v_attrs_dep, e_attrs_dep = create_acyclic_dep_tree(g, v_attrs, 'product')

    print(jgrapht.io.exporters.generate_dot(g_dep, v_attrs_dep, e_attrs_dep))
    # print(jgrapht.io.exporters.generate_gml(g_dep, per_vertex_attrs_dict=v_attrs_dep, per_edge_attrs_dict=e_attrs_dep))

if __name__ == "__main__":
    main()
