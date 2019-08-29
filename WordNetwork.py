from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QPixmap
import networkx as nx, shelve
import graphviz, tempfile
from collections import defaultdict
import os, sys

os.environ["PATH"] += os.pathsep + 'C:\\Program Files (x86)\\Graphviz2.38\\bin\\'
DEBUG = False

def load_words():
    words_by_len = {}
    file = open("usa.txt", "r")
    lines = file.readlines()
    for line in lines:
        word = line.strip().lower()
        if len(word) not in words_by_len:
            words_by_len[len(word)] = set()

        words_by_len[len(word)].add(word)

    return words_by_len


def construct_graph(words_by_len):
    G = nx.Graph()

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
                    debug("\t\t" + word + " -> " + reduced_word + " " + str(G[word][reduced_word]))

                # Words from changing a char at idx
                idx_modified_words = deletion_map[reduced_word][idx]
                for modified_word in idx_modified_words:
                    G.add_edge(word, modified_word, type='mod', index=idx, source=word[idx], dest=modified_word[idx])
                    debug("\t\t" + word + " -> " + modified_word + " " + str(G[word][modified_word]))

                deletion_map[reduced_word][idx].append(word)

    return G


def debug(msg):
    if DEBUG:
        print(msg)


def get_graph():
    graph_shelve = shelve.open("network_file")
    if 'graph' in graph_shelve:
        graph = graph_shelve['graph']
    else:
        words_by_len = load_words()
        graph = construct_graph(words_by_len)
        graph_shelve['graph'] = graph
    return graph


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "Word Transformation"
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.word_input = QLineEdit("lime", self)
        self.neighbor_button = QPushButton("Neighbors", self)
        self.neighbor_label = QLabel(self)
        self.neighbor_button.clicked.connect(self.on_button_draw_neighbors)

        self.from_input = QLineEdit("zipper", self)
        self.to_input = QLineEdit("monk", self)
        self.path_button = QPushButton("Find Paths", self)
        self.path_label = QLabel(self)
        self.path_button.clicked.connect(self.on_button_draw_path)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.word_input)
        left_layout.addWidget(self.neighbor_button)
        left_layout.addWidget(self.neighbor_label)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.from_input)
        right_layout.addWidget(self.to_input)
        right_layout.addWidget(self.path_button)
        right_layout.addWidget(self.path_label)

        layout = QHBoxLayout()
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        self.setLayout(layout)
        self.on_button_draw_neighbors()
        self.on_button_draw_path()
        self.show()


    def on_button_draw_neighbors(self):
        word = self.word_input.text()
        if word not in graph:
            self.neighbor_label.clear()
            return

        g = graphviz.Graph(format='svg', engine='sfdp')
        g.attr('graph', bgcolor='cyan', outputorder='edgesfirst')

        g.attr('node', fillcolor='yellow', style='filled')
        g.node(word)

        g.attr('node', fillcolor='white', style='filled')
        neighbors = graph[word]
        for n in neighbors:
            g.node(n)
            g.edge(word, n)

        graphviz_file = tempfile.mktemp('.gv')
        image = g.render(graphviz_file)
        pixmap = QPixmap(image)
        self.neighbor_label.setPixmap(pixmap)


    def on_button_draw_path(self):
        from_word = self.from_input.text()
        to_word = self.to_input.text()
        if from_word not in graph or to_word not in graph:
            self.path_label.clear()
            return

        paths = nx.all_shortest_paths(graph, source=from_word, target=to_word)

        g = graphviz.Graph(strict=True, format='svg', engine='dot')
        g.attr('graph', bgcolor='cyan', outputorder='edgesfirst')

        g.attr('node', fillcolor='yellow', style='filled')
        g.node(from_word)
        g.node(to_word)

        g.attr('node', fillcolor='white', style='filled')
        try:
            for path in paths:
                prev_node = None
                for node in path:
                    g.node(node)
                    if prev_node is not None:
                        g.edge(prev_node, node)
                    prev_node = node
        except nx.NetworkXNoPath:
            pass

        graphviz_file = tempfile.mktemp('.gv')
        image = g.render(graphviz_file)
        pixmap = QPixmap(image)
        self.path_label.setPixmap(pixmap)

if __name__ == "__main__":
    graph = get_graph()

    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
