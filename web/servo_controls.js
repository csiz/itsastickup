import {Plot} from "./plot.js"
import * as d3 from "d3"
import * as _ from "lodash"

export class ServoControls {
  constructor(selector, name, send, {n_servos=4, history=10}={}) {

    this.n_servos = n_servos;
    this.history = history;

    // Initialize plots

    this.div = d3.select(selector);

    this.servos = _.range(1, n_servos+1).map(i => {

      let servo_div = this.div.append("div");

      let title = servo_div.append("h3").text(`${name} ${i}`);

      let slider = servo_div.append("input")
      .attr("type", "range")
      .attr("min", 0)
      .attr("max", 1)
      .attr("step", 0.1)
      .attr("value", 0.5)
      .style("width", "400px");


      let position_plot = new Plot({
        svg: servo_div.append("svg"),
        width: 400, height: 200,
        xlabel: "Time (s)",
        xlim: [-history, 0],
        ylabel: "Position",
        ylim: [0, 1],
      });

      let last_position = null;
      let current_position = null;

      let positions = [];

      // Update the servo position and make it sticky. But only update every 100ms.
      slider.on("input", _.throttle(event => {
        let value = _.clamp(slider.node().value, 0, 1);
        send("move-servo", {n: i, position: value, sticky: 5});
      }, 100));

      return {
        positions,
        last_position,
        current_position,
        slider,
        title,
        servo_div,
        position_plot,
      };
    });

  }

  add_position({n, position, time}) {

    let servo = this.servos[n-1];

    servo.positions.push({position, time});
    servo.current_position = position;

    servo.slider.node().value = position;

    // Let the re-draw and fitlering occur on the time update.
    this.update_time(time);
  }

  update_time(time) {
    for (let servo of this.servos) {

      // Only keep recent positions.

      servo.positions = servo.positions.filter(({position, time: position_time}) => {
        let keep = position_time >= time - this.history;
        if (!keep) servo.last_position = position;
        return keep;
      });

      // Plot the position lines. Also plot the last value we received from the servo at the end.

      let position_points = [];

      if (servo.last_position !== null) {
        position_points.push({x: -this.history, y: servo.last_position});
      }

      for (let {position, time: pos_time} of servo.positions) {
        position_points.push({x: pos_time - time, y: position});
      }

      if (servo.current_position !== null) {
        position_points.push({x: 0, y: servo.current_position});
      }

      if (position_points.length > 0) servo.position_plot.draw_lines([position_points]);
    }
  }
}