import sys
from PyQt5.QtWidgets import QSizePolicy, QApplication, QGridLayout, QMessageBox, QTextEdit, QWidget, QInputDialog, QCheckBox, QRadioButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QPainter, QPen, QFont
import math
import heapq


class Graph:
    def __init__(self, directed=True):
        self.directed = directed
        self.nodes = []
        self.edges = {}


    def add_node(self, key, value=None):
        if value is None:
            value = key
        self.nodes.append({'key': key, 'value': value})
        

    def add_edge(self, a, b, weight=None):
        self.edges[(a, b)] = {'a': a, 'b': b, 'weight': weight}
        if not self.directed:
            self.edges[(b, a)] = {'a': b, 'b': a, 'weight': weight}


    def remove_node(self, key):
        self.nodes = [n for n in self.nodes if n['key'] != key]
        self.edges = {k: v for k, v in self.edges.items() if key not in k}

        old_keys = sorted(node['key'] for node in self.nodes)
        temp_edges = {old_key: new_key + 1 for new_key, old_key in enumerate(old_keys)}

        for node in self.nodes:
            node['key'] = temp_edges[node['key']]
            node['value'] = node['key']

        updated_edges = {}
        for (a, b), edge in self.edges.items():
            updated_edges[(temp_edges[a], temp_edges[b])] = {
                'a': temp_edges[a], 'b': temp_edges[b], 'weight': edge['weight']
            }
        self.edges = updated_edges


    def remove_edge(self, a, b):
        del self.edges[(a, b)]
        if not self.directed:
            del self.edges[(b, a)]


    def find_node(self, key):
        return next((n for n in self.nodes if n['key'] == key), None)


    def has_edge(self, a, b):
        return (a, b) in self.edges


    def set_edge_weight(self, a, b, weight):
        self.edges[(a, b)] = {'a': a, 'b': b, 'weight': weight}
        if not self.directed:
            self.edges[(b, a)] = {'a': b, 'b': a, 'weight': weight}


    def get_edge_weight(self, a, b):
        return self.edges.get((a, b), {}).get('weight')


    def get_graph_weight(self):
        s = 0
        for edge in self.edges:
            if not self.edges[edge]['weight']:
               return False
            else:
                s += self.edges[edge]['weight']
        if self.directed:
            return s
        else:
            return s/2
        
    def adjacent(self, key):
        return [b for (a, b), edge in self.edges.items() if a == key]


    def indegree(self, key):
        return sum(1 for edge in self.edges if edge[1] == key)


    def outdegree(self, key):
        return sum(1 for edge in self.edges if edge[0] == key)
    

    def is_connected(self):
        if not self.nodes:
            return True
        visited = self.dfs(self.nodes[0], set())
        return len(visited) == len(self.nodes)
    

    def is_eulerian(self):
        if not self.nodes:
            return False
        
        if self.directed is False:
            for node in self.nodes:
                if self.outdegree(node['key']) % 2 != 0 or self.outdegree(node['key']) == 0:
                    return False
                visited = self.dfs(self.nodes[0], set())
            return True, visited

        for node in self.nodes:
            if self.indegree(node['key']) != self.outdegree(node['key']):
                return False
        
        visited = self.dfs(self.nodes[0], set())
        
        if len(visited) != len(self.nodes):
            return False
         
        reverse_visited = set()
        visited = self.reverse_dfs(self.nodes[0], reverse_visited)
        
        return len(reverse_visited) == len(self.nodes), visited
    

    def is_hamilton(self):
        if not self.nodes:
            return False, {}

        node_keys = [node['key'] for node in self.nodes]
        n = len(node_keys)

        def is_valid(v, pos, path):
            if (path[pos-1], v) not in self.edges:
                return False

            if v in path:
                return False

            return True
        
        def find_cycle(path, pos):
            if pos == len(path):
                return (path[0], path[-1]) in self.edges

            for v in node_keys:
                if is_valid(v, pos, path):
                    path[pos] = v
                    if find_cycle(path, pos + 1):
                        return True
                    path[pos] = -1

            return False

        path = [-1] * n
        path[0] = node_keys[0]

        if find_cycle(path, 1):
            return True, set(path)

        return False, {}
    

    def is_tree(self):
        if self.is_connected is False:
            return False
        if self.directed and len(self.edges) != len(self.nodes)-1:
            return False
        if not self.directed and len(self.edges)/2 != len(self.nodes)-1:
            return False
        return True
    
 

    def dfs(self, node, visited):
        visited.add(node['key'])
        for neighbor in self.adjacent(node['key']):
            if neighbor not in visited:
                self.dfs(self.find_node(neighbor), visited)
        return visited
        

    def reverse_dfs(self, node, visited):
        visited.add(node['key'])
        for (a, b), edge in self.edges.items():
            if b == node['key'] and a not in visited:
                self.reverse_dfs(self.find_node(a), visited)
        return visited


    def dijkstra(self, start_key):
        queue = [(0, start_key)]
        distances = {node['key']: float('inf') for node in self.nodes}
        distances[start_key] = 0
        previous_nodes = {node['key']: None for node in self.nodes}

        while queue:
            current_distance, current_node = heapq.heappop(queue)
            if current_distance > distances[current_node]:
                continue

            for neighbor in self.adjacent(current_node):
                weight = self.get_edge_weight(current_node, neighbor)
                if weight is not None:
                    distance = current_distance + weight
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous_nodes[neighbor] = current_node
                        heapq.heappush(queue, (distance, neighbor))
        return distances
    

class DrawingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.node_centers = {}
        self.edges_coords = []
        self.active_radio_button = None
        self.state = None
        self.node_radius = 20


    def mousePressEvent(self, event):
        if not self.active_radio_button or not self.active_radio_button.isChecked():
            return

        action = self.active_radio_button.text()
        clicked_point = event.pos()
        closest_node_index = self.find_closest_node(clicked_point)

        actions = {
            "Add node": self.add_node,
            "Remove node": self.remove_node,
            "Add edge": self.add_edge,
            "Remove edge": self.remove_edge,
            "Remove Weight": self.remove_weight,
            "Add Weight": self.add_weight,
        }

        a = actions.get(action)
        if a:
            a(clicked_point, closest_node_index)

        self.update()


    def add_node(self, clicked_point, closest_node_index):
        new_node_key = len(gr.nodes) + 1
        gr.add_node(new_node_key)
        self.node_centers[new_node_key] = clicked_point
        self.parent().update_info_panel()


    def remove_node(self, clicked_point, closest_node_index):
        if closest_node_index is not None:
            node_key = closest_node_index
            gr.remove_node(node_key)
            self.edges_coords = [
                edge for edge in self.edges_coords
                if edge[0] != self.node_centers[node_key] and edge[1] != self.node_centers[node_key]
            ]
            self.node_centers.pop(node_key, None)
            values = list(self.node_centers.values())
            self.node_centers = {i + 1: values[i] for i in range(len(values))}
            self.parent().update_info_panel()


    def add_edge(self, clicked_point, closest_node_index):
        if self.state is not None:
            if closest_node_index is not None:
                start_node = self.state
                end_node = closest_node_index
                gr.add_edge(start_node, end_node)
                self.edges_coords[-1].append(self.node_centers[end_node])
                self.state = None
                self.parent().update_info_panel()
            else:
                self.edges_coords.pop()
                self.state = None
        elif closest_node_index is not None:
            self.state = closest_node_index
            self.edges_coords.append([self.node_centers[closest_node_index]])
            self.parent().update_info_panel()


    def remove_edge(self, clicked_point, closest_node_index):
        if self.state is not None:
            if closest_node_index is not None:
                start_node = self.state
                end_node = closest_node_index
                if gr.has_edge(start_node, end_node):
                    gr.remove_edge(start_node, end_node)
                    self.edges_coords = [
                        edge for edge in self.edges_coords
                        if edge[0] != self.node_centers[start_node] or edge[1] != self.node_centers[end_node]
                    ]
                if gr.has_edge(end_node, start_node):
                    gr.remove_edge(end_node, start_node)
                    self.edges_coords = [
                        edge for edge in self.edges_coords
                        if edge[1] != self.node_centers[start_node] or edge[0] != self.node_centers[end_node]
                    ]
                self.state = None
                self.parent().update_info_panel()
            else:
                self.state = None
        elif closest_node_index is not None:
            self.state = closest_node_index
            self.parent().update_info_panel()


    def remove_weight(self, clicked_point, closest_node_index):
        if self.state is not None:
            if closest_node_index is not None:
                start_node = self.state
                end_node = closest_node_index
                if gr.has_edge(start_node, end_node) and gr.get_edge_weight(start_node, end_node):
                    gr.set_edge_weight(start_node, end_node, None)
                self.parent().update_info_panel()
            else:
                self.state = None
        elif closest_node_index is not None:
            self.state = closest_node_index
            self.parent().update_info_panel()


    def add_weight(self, clicked_point, closest_node_index):
        if self.state is not None:
            if closest_node_index is not None:
                start_node = self.state
                end_node = closest_node_index
                if gr.has_edge(start_node, end_node) or gr.has_edge(end_node, start_node):
                    self.input_weight(start_node, end_node)
                self.state = None
                self.parent().update_info_panel()
            else:
                self.state = None
        elif closest_node_index is not None:
            self.state = closest_node_index
            self.parent().update_info_panel()


    def input_weight(self, start_node, end_node):
        text, ok = QInputDialog.getText(self, 'Input Weight', 'Enter the weight of the edge:')
        if ok and text:
            try:
                weight = float(text)
                gr.set_edge_weight(start_node, end_node, weight)
            except ValueError:
                QMessageBox.critical(self, 'Invalid Input', 'Please enter a valid number.')


    def paintEvent(self, event):
        def calculate_node_line(center, point):
            direction = QPointF(point - center)
            length = math.sqrt(direction.x()**2 + direction.y()**2)
            if length == 0:
                return center
            direction /= length
            node_line = center + direction * self.node_radius
            return node_line

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Arial", 12))

        for key, center in self.node_centers.items():
            painter.setPen(QPen(Qt.black, 2))
            painter.drawEllipse(center, self.node_radius, self.node_radius)
            painter.setPen(QPen(Qt.red, 2))
            painter.drawText(center + QPoint(-2, 5), str(key))


        painter.setPen(QPen(Qt.black, 2))
        for edge in self.edges_coords:
            if len(edge) == 2:
                start_point = edge[0]
                end_point = edge[1]
                if start_point == end_point:
                    start_point = QPoint(start_point.x(), start_point.y() - int(self.node_radius * 1.5))
                    painter.drawEllipse(start_point, self.node_radius // 2, self.node_radius // 2)
                else:
                    start_line = calculate_node_line(start_point, end_point)
                    end_line = calculate_node_line(end_point, start_point)

                    painter.drawLine(start_line, end_line)
                    if gr.directed:
                        direction = QPointF(end_line - start_line)
                        length = math.sqrt(direction.x()**2 + direction.y()**2)
                        direction /= length

                        arrow_points = [
                            end_line,
                            end_line - direction * 10 + QPointF(direction.y(), -direction.x()) * 5,
                            end_line - direction * 10 + QPointF(-direction.y(), direction.x()) * 5
                        ]

                        painter.drawPolygon(*arrow_points)

                start_node = self.find_closest_node(start_point)
                end_node = self.find_closest_node(end_point)
                if gr.has_edge(start_node, end_node) and gr.get_edge_weight(start_node, end_node):
                    painter.setPen(QPen(Qt.red, 2))
                    painter.drawText((start_point + end_point) / 2, str(gr.get_edge_weight(start_node, end_node)))
                    painter.setPen(QPen(Qt.black, 2))


    def find_closest_node(self, point):
        for key, center in self.node_centers.items():
            if (center - point).manhattanLength() <= self.node_radius:
                return key
        return None


class GraphApp(QWidget):
    def __init__(self):
        super().__init__()
        self.directedButton = None
        self.radio_buttons = []
        self.text_field = None
        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 800, 800)
        self.setWindowTitle('Graph Playground')

        drawing_panel = DrawingPanel(self)
        actions_panel = self.create_action_panel("Actions", (QSizePolicy.Expanding, QSizePolicy.Fixed))
        info_panel = self.create_info_panel('Info', (QSizePolicy.Expanding, QSizePolicy.Fixed))

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(drawing_panel)
        main_layout.addWidget(actions_panel)
        main_layout.addWidget(info_panel)
        self.setLayout(main_layout)

        self.show()

    def create_action_panel(self, title, size_policy=None):
        panel = QWidget(self)
        panel.setStyleSheet("background-color: lightGray; border: 1px solid gray;")
        panel.setFixedHeight(100)
        panel.setFixedWidth(800)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        panel_title = QLabel(title)
        panel_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(panel_title, alignment=Qt.AlignCenter)
        
        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        button_names = ['Add node', 'Remove node', 'Add edge', 'Remove edge', 'Add Weight', 'Remove Weight']
        for i, name in enumerate(button_names):
            radio_button = QRadioButton(name)
            radio_button.clicked.connect(self.radio_button_clicked)
            self.radio_buttons.append(radio_button)
            grid_layout.addWidget(radio_button, i // 2, i % 2)

        self.directedButton = QCheckBox('Directed')
        self.directedButton.setChecked(True)
        self.directedButton.stateChanged.connect(self.update_directed)
        grid_layout.addWidget(self.directedButton, 3, 0)

        if size_policy:
            panel.setSizePolicy(*size_policy)

        return panel

    def create_info_panel(self, title, size_policy=None):
        panel = QWidget(self)
        panel.setStyleSheet("background-color: lightGray; border: 1px solid gray;")
        panel.setMaximumHeight(150)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        panel_title = QLabel(title)
        panel_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(panel_title)

        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        layout.addWidget(self.text_field)

        if size_policy:
            panel.setSizePolicy(*size_policy)

        return panel

    def radio_button_clicked(self):
        sender = self.sender()
        if sender.isChecked():
            drawing_panel = self.findChild(DrawingPanel)
            drawing_panel.active_radio_button = sender
            drawing_panel.update()


    def update_directed(self, state):
        directed = (state == Qt.Checked)
        gr.directed = directed
        self.findChild(DrawingPanel).update()


    def update_info_panel(self):
        if len(gr.nodes) > 0:
            self.directedButton.setDisabled(True)
        else:
            self.directedButton.setDisabled(False)

        try:
            is_eulerian, eulerian_cycle = gr.is_eulerian()
        except TypeError:
            is_eulerian, eulerian_cycle = gr.is_eulerian(), {}

        graph_weight = gr.get_graph_weight()
        dijkstra_distances = gr.dijkstra(1)
        dijkstra_distances_text = '\n            '.join(
            f'Way (1, {x}): {dist}' for x, dist in dijkstra_distances.items() if dist < float('inf')
        )

        info = (
            f"Nodes: {[x['value'] for x in gr.nodes]}\n"
            f"Edges: {list(gr.edges.keys())}\n"
            f"Connected: {gr.is_connected()}\n"
            f"Eulerian: {is_eulerian}\n"
            f"Eulerian cycle: {eulerian_cycle}\n"
            f"Hamilton: {gr.is_hamilton()[0]}\n"
            f"Hamilton cycle: {gr.is_hamilton()[1]}\n"
            f"Tree: {gr.is_tree()}\n"
            f"Graph Weight: {graph_weight if graph_weight else 'Add weights for all edges'}\n"
            f"Weights of shortest ways (Dijkstra algorithm):\n{dijkstra_distances_text}\n"
        )
        self.text_field.setPlainText(info)



if __name__ == '__main__':
    gr = Graph(directed=True)
    app = QApplication(sys.argv)
    main_window = GraphApp()
    sys.exit(app.exec_())
