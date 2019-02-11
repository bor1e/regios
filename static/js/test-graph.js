/**
 * This example shows the available edge label renderers for the canvas
 * renderer.
 */
var i,
    s,
    N = 2,
    E = 10,
    L = 3,
    g = {
      nodes: [],
      edges: []
    };
// Generate a random graph:
for (i = 0; i < N; i++)
  g.nodes.push({
    id: 'n' + i,
    label: 'Node ' + i,
    x: Math.random(),
    y: Math.random(),
    size: Math.random(),
    color: '#666'
  });
for (i = 0; i < E; i++)
  g.edges.push({
    id: 'e' + i,
    label: 'Edge ' + i,
    source: 'n0',
    target: 'n1',
    size: 1,
    color: '#ccc',
    type: 'curvedArrow',
    count: i
  });
for (i = 0; i < L; i++)
  g.edges.push({
    id: 'e_loop' + i,
    label: 'Edge_loop ' + i,
    source: 'n0',
    target: 'n0',
    size: 1,
    color: '#ccc',
    type: 'curvedArrow',
    count: i
  });
// Instantiate sigma:
s = new sigma({
  graph: g,
  renderer: {
    container: document.getElementById('graph-container'),
    type: 'canvas'
  }
});