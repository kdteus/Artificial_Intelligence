"""Register search algorithms once; the UI and problems consume this registry."""

from .search import breadth_first_search, depth_first_search

ALGORITHMS = {
    "BFS": {
        "search": breadth_first_search,
        "subtitle": "Duyệt theo từng lớp · tìm đường ngắn nhất",
        "theme": "blue",
    },
    "DFS": {
        "search": depth_first_search,
        "subtitle": "Đi sâu theo nhánh · quay lui",
        "theme": "purple",
    },
}
