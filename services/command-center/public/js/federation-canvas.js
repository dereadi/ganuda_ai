// Federation Canvas — D3.js Interactive Graph (AppRegistry version)

(function() {
    const app = {
        id: 'federation-canvas',
        title: 'Federation Canvas',
        tags: ['federation', 'canvas', 'graph', 'd3', 'network', 'nodes'],
        _canvas: null,

        open(savedPos) {
            if (WindowManager.exists(this.id)) {
                WindowManager.focus(this.id);
                return;
            }
            WindowManager.create({
                id: this.id,
                title: this.title,
                width: savedPos?.width || 1000,
                height: savedPos?.height || 700,
                x: savedPos?.x || 50,
                y: savedPos?.y || 50,
                html: '<div id="federation-canvas-container" style="width:100%;height:100%;background:#0a0a0a;"></div>',
                onclose: () => this.cleanup()
            });
            setTimeout(() => this.init(), 100);
        },

        init() {
            const container = document.getElementById('federation-canvas-container');
            if (!container) return;
            const width = container.clientWidth;
            const height = container.clientHeight;

            const svg = d3.select(container)
                .append('svg').attr('width', width).attr('height', height);

            const zoom = d3.zoom().scaleExtent([0.5, 3])
                .on('zoom', (event) => g.attr('transform', event.transform));
            svg.call(zoom);

            const g = svg.append('g');

            svg.append('defs').append('marker')
                .attr('id', 'arrowhead').attr('viewBox', '-0 -5 10 10')
                .attr('refX', 20).attr('refY', 0).attr('orient', 'auto')
                .attr('markerWidth', 6).attr('markerHeight', 6)
                .append('svg:path').attr('d', 'M 0,-5 L 10,0 L 0,5')
                .attr('fill', '#D2691E').style('stroke', 'none');

            this._svg = svg;
            this._g = g;
            this._width = width;
            this._height = height;

            this.loadGraph();
        },

        async loadGraph() {
            let nodes, links;
            try {
                const data = await FlowCore.api('/api/federation/summary');
                // Build nodes from federation summary
                nodes = (data.nodes || []).map(n => ({
                    id: n.node_id || n.name,
                    name: n.name || n.node_id,
                    ip: n.ip || '',
                    platform: n.platform || 'Linux',
                    status: n.status || 'unknown',
                    jrs: n.jrs_running || [],
                    x: this._width / 2 + (Math.random() - 0.5) * 200,
                    y: this._height / 2 + (Math.random() - 0.5) * 200
                }));
            } catch (e) {
                // Fallback: real federation node list
                nodes = [
                    {id: 'redfin', name: 'Redfin (GPU)', ip: '192.168.132.223', platform: 'Linux', status: 'online'},
                    {id: 'bluefin', name: 'Bluefin (DB)', ip: '192.168.132.222', platform: 'Linux', status: 'online'},
                    {id: 'greenfin', name: 'Greenfin (Bridge)', ip: '192.168.132.224', platform: 'Linux', status: 'online'},
                    {id: 'owlfin', name: 'Owlfin (DMZ)', ip: '192.168.132.170', platform: 'Linux', status: 'online'},
                    {id: 'eaglefin', name: 'Eaglefin (DMZ)', ip: '192.168.132.84', platform: 'Linux', status: 'online'},
                    {id: 'bmasass', name: 'bmasass (Mobile)', ip: '192.168.132.21', platform: 'macOS', status: 'online'}
                ].map(n => ({ ...n, jrs: [], x: this._width/2 + (Math.random()-0.5)*200, y: this._height/2 + (Math.random()-0.5)*200 }));
            }

            links = [
                {source: 'bluefin', target: 'redfin', channel: 'db'},
                {source: 'bluefin', target: 'greenfin', channel: 'db'},
                {source: 'redfin', target: 'owlfin', channel: 'web'},
                {source: 'redfin', target: 'eaglefin', channel: 'web'},
                {source: 'greenfin', target: 'bluefin', channel: 'pii'},
                {source: 'bmasass', target: 'redfin', channel: 'tailscale'},
                {source: 'owlfin', target: 'eaglefin', channel: 'keepalived'}
            ].filter(l => nodes.some(n => n.id === l.source) && nodes.some(n => n.id === l.target));

            this._nodes = nodes;
            this._links = links;
            this.renderGraph();
        },

        renderGraph() {
            const g = this._g;
            const nodes = this._nodes;
            const links = this._links;

            const simulation = d3.forceSimulation(nodes)
                .force('link', d3.forceLink(links).id(d => d.id).distance(150))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(this._width / 2, this._height / 2))
                .force('collision', d3.forceCollide().radius(60));

            const link = g.append('g').selectAll('line').data(links).enter()
                .append('line').attr('stroke', '#D2691E').attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)');

            const node = g.append('g').selectAll('g').data(nodes).enter().append('g')
                .call(d3.drag()
                    .on('start', (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
                    .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
                    .on('end', (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

            const colors = { redfin: '#DC143C', bluefin: '#4169E1', greenfin: '#32CD32', owlfin: '#9370DB', eaglefin: '#FF8C00', bmasass: '#8B4513' };

            node.append('circle').attr('r', 40)
                .attr('fill', d => colors[d.id] || '#888')
                .attr('stroke', '#FFF').attr('stroke-width', 3);

            node.append('text').text(d => d.id)
                .attr('text-anchor', 'middle').attr('dy', '.35em')
                .attr('fill', '#FFF').attr('font-size', '12px').attr('font-weight', 'bold');

            node.append('circle').attr('r', 8).attr('cx', 30).attr('cy', -30)
                .attr('fill', d => d.status === 'online' ? '#90EE90' : '#FF6B6B')
                .attr('stroke', '#000').attr('stroke-width', 2);

            node.on('click', (event, d) => {
                const jrs = d.jrs?.length ? d.jrs.join(', ') : 'None';
                alert(`${d.name}\nIP: ${d.ip}\nPlatform: ${d.platform}\nStatus: ${d.status}\nJrs: ${jrs}`);
            });

            simulation.on('tick', () => {
                link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });

            this._simulation = simulation;
        },

        cleanup() {
            if (this._simulation) this._simulation.stop();
            this._simulation = null;
        }
    };

    AppRegistry.register(app);
})();
