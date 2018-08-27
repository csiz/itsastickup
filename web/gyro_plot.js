import {Plot} from "./plot.js"
import * as d3 from "d3"
import * as _ from "lodash"


export class GyroPlot{
  constructor(selector, name, {avg_duration=0.2}={}) {

    // Initialize plots

    this.div = d3.select(selector);

    this.div.append("h3").text(name);

    this.acceleration_plot = new Plot({
      svg: this.div.append("svg"),
      width: 600, height: 300,
      xlabel: "Time (s)",
      xlim: [-60, 0],
      ylabel: "Acceleration (N/s²)",
      ylim: [-16, +16],
    });

    this.rotation_plot = new Plot({
      svg: this.div.append("svg"),
      width: 600, height: 300,
      xlabel: "Time (s)",
      xlim: [-60, 0],
      ylabel: "Rotation (rad/s)",
      ylim: [-2*Math.PI, +2*Math.PI], // -1 to +1 rotations per second
    });

    // Initialize measures and averaging constants.
    this.measures = [];
    this.avg_duration = avg_duration;
  }

  add_measure(measure) {
    let {time: current_time} = measure;

    // If the last measure is very recent, do a weighted average so we don't
    // overload the browser by making it draw all the points.
    if (this.measures.length === 0) this.measures.push(measure);
    else {
      let last_measure = _.last(this.measures);
      let last_time = last_measure.time - last_measure.duration;
      if (current_time - last_time > this.avg_duration) this.measures.push(measure);
      else gyro_inplace_weighted_average(last_measure, measure);
    }


    // Only keep last 60 seconds of measures.
    this.measures = this.measures.filter(({time}) => time > current_time - 60.0);

    const axes = [0, 1, 2];

    // Draw acceleration and rotation.
    this.acceleration_plot.draw_lines(
      axes.map(axis_i => this.measures.map(m => ({x: m.time - current_time, y: m.acceleration[axis_i]}))),
    );

    this.rotation_plot.draw_lines(
      axes.map(axis_i => this.measures.map(m => ({x: m.time - current_time, y: m.rotation[axis_i]})))
    );
  }
}



function gyro_inplace_weighted_average(last_measure, measure) {
  let {
    acceleration: last_a,
    rotation: last_r,
    duration: last_d,
  } = last_measure;

  let {
    acceleration: a,
    rotation: r,
    duration: d,
  } = measure;

  let total_d = d + last_d;

  last_measure.duration = total_d;
  last_measure.time = measure.time;

  // Do a weighted average of acceleration and rotation for each axis.
  for (let i of [0, 1, 2]) {
    last_measure.acceleration[i] = (last_a[i] * last_d + a[i] * d) / total_d;
    last_measure.rotation[i] = (last_r[i] * last_d + r[i] * d) / total_d;
  }
}