from functools import reduce

branch = '├'
pipe = '|'
end = '└'
dash = '─'


class Tree(object):
    def __init__(self, tag):
        self.tag = tag


class Node(Tree):
    def __init__(self, tag, *nodes):
        super(Node, self).__init__(tag)
        self.nodes = list(nodes)


class Leaf(Tree):
    pass


def _draw_tree(tree, level, last=False, sup=[]):
    dir_tree = ''
    def update(left, i):
        if i < len(left):
            left[i] = '   '
        return left

    dir_tree += (''.join(reduce(update, sup, ['{}  '.format(pipe)] * level)) \
          + (end if last else branch) + '{} '.format(dash) \
          + (str(tree.tag) + '/' if '.' not in str(tree.tag) else str(tree.tag)) + '\n')
    if isinstance(tree, Node):
        level += 1
        for node in tree.nodes[:-1]:
            dir_tree += _draw_tree(node, level, sup=sup)
        dir_tree += _draw_tree(tree.nodes[-1], level, True, [level] + sup)
    return dir_tree


def draw_tree(trees):
    dir_tree = '```\n'
    for tree in trees[:-1]:
        dir_tree += _draw_tree(tree, 0)
    dir_tree += _draw_tree(trees[-1], 0, True, [0])
    dir_tree += '```'
    return dir_tree

class Track(object):
    def __init__(self, parent, idx):
        self.parent, self.idx = parent, idx


def parser(text):
    trees = []
    tracks = {}
    for line in text.splitlines():
        line = line.strip()
        key, value = map(lambda s: s.strip(), line.split(':', 1))
        nodes = value.split()
        if len(nodes):
            parent = Node(key)
            for i, node in enumerate(nodes):
                tracks[node] = Track(parent, i)
                parent.nodes.append(Leaf(node))
            curnode = parent
            if curnode.tag in tracks:
                t = tracks[curnode.tag]
                t.parent.nodes[t.idx] = curnode
            else:
                trees.append(curnode)
        else:
            curnode = Leaf(key)
            if curnode.tag in tracks:
                # well, how you want to handle it?
                pass # ignore
            else:
                trees.append(curnode)
    return trees