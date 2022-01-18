import jgrapht
import jgrapht

filename="~/SurfDrive/Documents/ICT-for-industry/data/logging-log4j2-rel-2.12.1-rapid/rapid/org.apache.logging.log4j.log4j-iostreams-2.12.1-merged.json"

def main():
    g = jgrapht.create_graph(directed=True, weighted=True, allowing_self_loops=True, allowing_multiple_edges=False)
    jgrapht.io.importers.read_json(g, filename)

if __name__ == "__main__":
    main()
