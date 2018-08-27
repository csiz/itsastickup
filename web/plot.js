import "./plot.css"

import * as d3 from "d3"


export class Plot {
  constructor({
    svg,
    width=400, height=200,
    xlabel="x", xlim,
    ylabel="y", ylim,
    margin = {},
    padding = {},
  }={}) {

    margin = {top: 5, right: 5, bottom: 20, left: 25, ...margin};
    padding = {top: 5, right: 5, bottom: 5, left: 5, ...padding};

    if (!(svg instanceof d3.selection)) svg = d3.select(svg);

    this.svg = svg
      .classed("plot", true)
      .attr("width", width)
      .attr("height", height);

    this.xscale = d3.scaleLinear()
      .domain(xlim)
      .range([margin.left + padding.left, width - margin.right - padding.right]);

    this.yscale = d3.scaleLinear()
      .domain(ylim)
      .range([height - margin.bottom - padding.bottom, margin.top + padding.top]);


    this.xaxis = this.svg.append("g")
      .classed("axis", true)
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(this.xscale).tickSizeOuter(0));

    this.yaxis = this.svg.append("g")
      .classed("axis", true)
      .attr("transform", `translate(${margin.left}, 0)`)
      .call(d3.axisLeft(this.yscale).tickSizeOuter(0));


    this.xgrid = this.svg.append("g")
      .classed("grid", true)
      .attr("transform", `translate(0,${height - margin.bottom - padding.bottom})`)
      .call(d3.axisBottom(this.xscale)
        .tickSizeOuter(0)
        .ticks(5)
        .tickSizeInner(- (height - margin.top - margin.bottom - padding.top - padding.bottom))
        .tickFormat(""));
    this.xgrid.select(".domain").remove();


    this.ygrid = this.svg.append("g")
      .classed("grid", true)
      .attr("transform", `translate(${margin.left + padding.left}, 0)`)
      .call(d3.axisLeft(this.yscale)
        .tickSizeOuter(0)
        .ticks(5)
        .tickSizeInner(- (width - margin.right - margin.left - padding.right - padding.left))
        .tickFormat(""));
    this.ygrid.select(".domain").remove();

    this.xlabel = this.svg.append("text")
      .classed("label", true)
      .attr("transform", `translate(${width - margin.right}, ${height - margin.bottom - 3})`)
      .attr("text-anchor", "end")
      .text(xlabel);

    this.ylabel = this.svg.append("text")
      .classed("label", true)
      .attr("transform", `translate(${margin.left + 3}, ${margin.top})`)
      .attr("dominant-baseline", "alphabetic")
      .attr("writing-mode", "tb")
      .text(ylabel);
  }

  draw_lines(lines) {
    let line_spec = d3.line()
      .x(p => this.xscale(p.x))
      .y(p => this.yscale(p.y))
      .curve(d3.curveCatmullRom);

    let {created, all} = join_to_dom(this.svg, "path.line", lines);
    created
      .attr("stroke", (_, i) => d3.schemeCategory10[i%10])
      .attr("fill", "none")
      .attr("stroke-width", 1.5)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round");

    all
      .attr("d", line => line_spec(line));
  }
}


/**
 * Join an array of values to displayable elements in the document.
 * @param {*} root - Root DOM element to which we attach data.
 * @param {String} element - DOM elements that represent the data as "type.class".
 * @param {Array} data - Array of values to show on the DOM.
 */
function join_to_dom(root, element, data) {
  // Select the root if not already a d3 selection.
  if (!(root instanceof d3.selection)) root = d3.select(root);

  // Split the element description into type and name.
  let [type, name=null, ...other] = element.split(".");

  type = type.trim();
  if (name !== null) name.trim();

  if (other.length > 0) throw `The element selection must be of the form "type.class"; instead got: ${element}`

  // Join the data with the DOM.
  let data_join = root.selectAll(name !== null ? `${type}.${name}` : type).data(data);

  // Create new entries.
  let created = data_join.enter().append(type);
  if (name !== null) created.classed(name, true);

  // Select all existing element.
  let all = created.merge(data_join);

  // Remove deleted elements.
  data_join.exit().remove();

  // Return for further modifications.
  return {created, all};
}
