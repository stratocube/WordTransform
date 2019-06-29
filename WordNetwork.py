from PyQt5.QtWidgets import QApplication, QLabel
import networkx as nx
import matplotlib.pyplot as plt
import py_graphviz
from networkx.drawing.nx_agraph import graphviz_layout
from collections import defaultdict
from itertools import groupby

DEBUG = False


def load_words():
    words_by_len = {}
    #file = open("words.txt", "r")
    file = open("usa.txt", "r")
    lines = file.readlines()
    for line in lines:
        word = line.strip().lower()
        if len(word) not in words_by_len:
            words_by_len[len(word)] = set()

        words_by_len[len(word)].add(word)

    return words_by_len


def construct_graph(words_by_len):
    G = nx.DiGraph()

    for length in words_by_len:
        if length < 3:
            continue
        debug(str(length) + " letter words:")

        deletion_map = defaultdict(lambda: defaultdict(list))

        for word in words_by_len[length]:
            G.add_node(word)
            debug("\t" + word)

            for idx in range(length):
                reduced_word = word[:idx] + word[idx+1:]

                # Words from removing a char at idx
                if length != 3 and length-1 in words_by_len and reduced_word in words_by_len[length-1]:
                    G.add_edge(word, reduced_word, type='del', index=idx, char=word[idx])
                    G.add_edge(reduced_word, word, type='ins', index=idx, char=word[idx])
                    debug("\t\t" + word + " -> " + reduced_word + " " + str(G[word][reduced_word]))
                    debug("\t\t" + reduced_word + " -> " + word + " " + str(G[reduced_word][word]))

                # Words from changing a char at idx
                idx_modified_words = deletion_map[reduced_word][idx]
                for modified_word in idx_modified_words:
                    G.add_edge(word, modified_word, type='mod', index=idx, source=word[idx], dest=modified_word[idx])
                    G.add_edge(modified_word, word, type='mod', index=idx, source=modified_word[idx], dest=word[idx])
                    debug("\t\t" + word + " -> " + modified_word + " " + str(G[word][modified_word]))
                    debug("\t\t" + modified_word + " -> " + word + " " + str(G[modified_word][word]))

                deletion_map[reduced_word][idx].append(word)

    return G


def debug(msg):
    if DEBUG:
        print(msg)


def main():
    words_by_len = load_words()
    graph = construct_graph(words_by_len)

    '''
    u_graph = nx.to_undirected(graph)
    for component in nx.connected_components(u_graph):
        debug(len(component))
    print("done")
    '''
    selection = "block"

    plt.subplot(121)
    paths = nx.single_source_shortest_path(graph, selection, 2)
    subg = graph.subgraph(paths)
    shells = [list(g) for k, g in groupby(paths, lambda s: len(paths[s]))]
    print(shells)
    pos = nx.shell_layout(subg, shells, scale=3)
    pos = graphviz_layout(subg, prog='twopi', args='')
    nx.draw(subg, pos=pos, node_size=20, with_labels=True, font_weight='bold')
    plt.axis('equal')
    plt.show()

    '''
    app = QApplication([])
    label = QLabel('Hello!')
    label.show()
    app.exec_()
    '''


if __name__ == "__main__":
    main()
