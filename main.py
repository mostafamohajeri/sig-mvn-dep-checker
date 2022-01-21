from operator import is_
import jgrapht
import jgrapht.drawing.draw_matplotlib as drawing
import json

import matplotlib.pyplot as plt

filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-docker-2.12.1-reduced.json"
# filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-couchdb-2.12.1-merged.json"
# filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-perf-2.12.1-merged.json"
# filename = "./data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-cassandra-2.12.1-merged.json"
v_attrs = {}

def add_node_dep(g, node_id, mapping, v_attrs_glob, v_attrs, attr):
    """ Add node function for dep graph """
    node_name = v_attrs_glob[node_id][attr]

    if node_name not in mapping:
        mapping.append(node_name)
        new_node = mapping.index(node_name)
        g.add_vertex(new_node)
        v_attrs[new_node] = {}
        v_attrs[new_node][attr] = v_attrs_glob[node_id][attr]
        v_attrs[new_node]["application_node"] = v_attrs_glob[node_id]["application_node"]
        v_attrs[new_node]["label"] = v_attrs_glob[node_id][attr]
        v_attrs[new_node]["vulnerabilities"] = {}

    else:
        new_node = mapping.index(node_name)

    meta = json.loads(v_attrs_glob[node_id]['metadata'])
    if "vulnerabilities" in meta.keys():
        vuln = meta["vulnerabilities"]
        for k in vuln.keys():
            v_attrs[new_node]["vulnerabilities"][k] = vuln[k]

    return new_node

def create_external_dependencies(g, v_attrs_glob, attr):
    """ create a dep graph """
    e_attrs = {}
    v_attrs = {}

    mapping = []
    g_dep = jgrapht.create_graph(directed=True, weighted=False,
                                 allowing_self_loops=True, allowing_multiple_edges=False, any_hashable=False)
    for e in g.edges:
        if not (v_attrs_glob[g.edge_target(e)][attr] == v_attrs_glob[g.edge_source(e)][attr]):
            src = v_attrs_glob[g.edge_source(e)][attr]
            dst = v_attrs_glob[g.edge_target(e)][attr]

            src = add_node_dep(g_dep, g.edge_source(e), mapping, v_attrs_glob, v_attrs, attr)
            dst = add_node_dep(g_dep, g.edge_target(e), mapping, v_attrs_glob, v_attrs, attr)

            # Add edge if not in graph 
            if not g_dep.contains_edge_between(src, dst):
                tmp = g_dep.add_edge(src, dst)
                e_attrs[tmp] = {}
                e_attrs[tmp]['count'] = 1
            else:
                for tmp_edge in g_dep.edges_between(src, dst):
                    e_attrs[tmp_edge]['count'] += 1

    return g_dep, v_attrs, e_attrs, mapping


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


def add_node(g, node_name, attributes, attr, node_attr):
    """" Add a node to g return node id """
    node_id = g.add_vertex()

    attributes[node_id] = {}
    attributes[node_id]['label'] = node_name
    attributes[node_id][attr] = node_name
    for k in node_attr.keys():
        attributes[node_id][k] = node_attr[k]

    return node_id


def add_edge(g, src, dst, e_attrs, edge_attr):
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
    for k in edge_attr.keys():
        e_attrs[edge][k] = edge_attr[k]


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


def add_external_dep_for_attr(t_dep, vt_attrs, et_attrs, g_dep, v_attrs_dep, e_attrs_dep, dep_mapping, node_id, path, attr_filter):
    v = dep_mapping.index(vt_attrs[node_id][attr_filter]) 
    for e in g_dep.outedges_of(v):
        target_name = v_attrs_dep[g_dep.edge_target(e)][attr_filter]

        if v_attrs_dep[v][attr_filter] != target_name:
            if v_attrs_dep[g_dep.edge_target(e)][attr_filter] not in path:
                edge = find_out_target(t_dep, node_id, target_name, vt_attrs)
                if not edge :
                    target = add_node(t_dep, target_name, vt_attrs, attr_filter, v_attrs_dep[g_dep.edge_target(e)])
                    add_edge(t_dep, node_id, target, et_attrs, e_attrs_dep[e])
                else:
                    et_attrs[edge]['count'] += 1


def rec_create_acyclic_dep_tree(t_dep, vt_attrs, et_attrs, g_dep, v_attrs_dep, e_attrs_dep, dep_mapping, node_id, path, attr_filter):

    path.append(vt_attrs[node_id][attr_filter])
    add_external_dep_for_attr(t_dep, vt_attrs, et_attrs, g_dep, v_attrs_dep, e_attrs_dep, dep_mapping, node_id, path, attr_filter)

    for e in t_dep.outedges_of(node_id):
        target = t_dep.edge_target(e)
        rec_create_acyclic_dep_tree(t_dep, vt_attrs, et_attrs, g_dep, v_attrs_dep, e_attrs_dep, dep_mapping, target, path, attr_filter)

    path.pop()


def create_acyclic_dep_tree(g_dep, v_attrs_dep, e_attrs_dep, dep_mapping, attr_filter):
    """ Create an acyclic dependency tree off the components in g with the granularity of attr_filter"""
    vt_attrs = {}
    et_attrs = {}
    node_mapping = []
    roots = []

    t_dep = jgrapht.create_graph(directed=True, weighted=False,
                                 allowing_self_loops=False, allowing_multiple_edges=False, any_hashable=False)


    # Find direct dependancies of the appliction
    for v in g_dep.vertices:
        if v_attrs_dep[v]['application_node']:
            node_name = v_attrs_dep[v][attr_filter]

            if node_name not in roots:
                roots.append(node_name)
            if node_name not in node_mapping:
                node_mapping.append(add_node(t_dep, node_name, vt_attrs, attr_filter, v_attrs_dep[v]))

    # # Go to last layer and check for direct dependancies in there that are not in the path to root
    # print(roots)
    for i in range(len(roots)):
        rec_create_acyclic_dep_tree(t_dep, vt_attrs, et_attrs, g_dep, v_attrs_dep, e_attrs_dep, dep_mapping, node_mapping[i], [], attr_filter)

    return t_dep, vt_attrs, et_attrs


def main():
    g = jgrapht.create_graph(directed=True, weighted=False,
                             allowing_self_loops=True, allowing_multiple_edges=False, any_hashable=False)
    jgrapht.io.importers.read_json(g, filename,
                                   import_id_cb=import_id_cb,
                                   vertex_attribute_cb=vertex_attribute_cb)

    # ext_depend_graph = draw_external_dependencies(g, v_attrs)
    attr = 'product'

    g_dep, v_attrs_dep, e_attrs_dep, mapping = create_external_dependencies(g, v_attrs, attr)
    t_dep, vt_attrs_dep, et_attrs_dep = create_acyclic_dep_tree(g_dep, v_attrs_dep, e_attrs_dep, mapping, attr)

    print(jgrapht.io.exporters.generate_dot(t_dep, vt_attrs_dep, et_attrs_dep))
    # print(jgrapht.io.exporters.generate_gml(g_dep, per_vertex_attrs_dict=v_attrs_dep, per_edge_attrs_dict=e_attrs_dep))



if __name__ == "__main__":
    main()
