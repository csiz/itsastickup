import * as d3 from "d3"

export class Plot {
  constructor({
      svg,
      width, height,
      xlabel, xlim,
      ylabel, ylim,
      margin = {left: 40, right: 10, top: 10, bottom: 40},
  }) {

    this.svg = svg.attr("width", width).attr("height", height);

    this.xscale = d3.scaleLinear()
      .domain(xlim)
      .range([margin.left, width - margin.right]);

    this.yscale = d3.scaleLinear()
      .domain(ylim)
      .range([height - margin.bottom, margin.top]);


    this.xaxis = this.svg.append("g").classed("xaxis", true)
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(this.xscale));

    this.yaxis = this.svg.append("g").classed("yaxis", true)
      .attr("transform", `translate(${margin.left}, 0)`)
      .call(d3.axisLeft(this.yscale));


    this.xlabel = this.svg.append("text")
      .attr("transform", `translate(${width*0.5},${height - margin.bottom + 30})`)
      .style("text-anchor", "middle")
      .text(xlabel);

    this.ylabel = this.svg.append("text")
      .attr("transform", `translate(${+15}, ${height * 0.5}) rotate(-90)`)
      .style("text-anchor", "middle")
      .text(ylabel);


  }

  draw_lines({lines}) {
    let line_spec = d3.line()
      .x(p => this.xscale(p.x))
      .y(p => this.yscale(p.y))
      .curve(d3.curveCardinal);

    join_data({
      root: this.svg,
      name: "line",
      type: "path",
      data: lines,
      create: function(line, i){
        d3.select(this)
          .attr("stroke", d3.schemeCategory10[i%10])
          .attr("fill", "none")
          .attr("stroke-width", 1.5)
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round");
      },
      state: function(line, i){
        d3.select(this)
          .attr("d", line_spec(line));
      }

    })
  }
}







// Re-write the update pattern in a form that makes it easier to work with.
function join_data({root, name, type, data, create, state, created_call}) {
  let data_join = root.selectAll(`${type}.${name}`).data(data);
  let created = data_join.enter().append(type).classed(name, true).each(create);
  if (created_call) created.call(created_call);
  let current = created.merge(data_join);
  data_join.exit().remove();
  current.each(state);
}