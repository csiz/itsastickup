import "./style.css"

import _ from "lodash"
import * as d3 from "d3"

import {Plot} from "./plots.js"
import { SSL_OP_EPHEMERAL_RSA } from "constants";

// Setup
// -----

const socket = new WebSocket("ws://192.168.1.8:45223");

const connected = new Promise(function(resolve, reject){
  socket.onopen = resolve
  socket.onerror = reject
})

const send = (event, data) => socket.send(JSON.stringify([event, data]))


const on = (event, callback) => {
  send("subscribe", event)

  socket.onmessage = (message) => {
    const [received_event, received_data] = JSON.parse(message.data)
    if (received_event === event) callback(received_data)
  }
}


// ### Gyro display

let gyro_0 = d3.select("main").append("div")
  .attr("id", "gyro-0");
gyro_0.append("h3").text("Gyro-0");

let gyro_0_accel = new Plot({
  svg: gyro_0.append("svg"),
  width: 800, height: 400,
  xlabel: "Time (s)",
  xlim: [-60, 0],
  ylabel: "Acceleration (N/s^2)",
  ylim: [-16, +16],
});

let gyro_0_rot = new Plot({
  svg: gyro_0.append("svg"),
  width: 800, height: 400,
  xlabel: "Time (s)",
  xlim: [-60, 0],
  ylabel: "Rotation (rad/s)",
  ylim: [-2*Math.PI, +2*Math.PI],
});


let measures = [];

let measure_avg_over = 0.2;

function add_measure(measure) {
  let {time: current_time} = measure;

  // If the last measure is very recent, do a weighted average so we don't
  // overload the browser by making it draw all the points.
  if (measures.length === 0) measures.push(measure);
  else {
    let last_measure = measures[measures.length - 1];
    let last_time = last_measure.time - last_measure.duration;
    if (current_time - last_time > measure_avg_over) measures.push(measure);
    else gyro_inplace_weighted_average(last_measure, measure);
  }


  // Only keep last 60 seconds of measures.
  measures = measures.filter(({time}) => time > current_time - 60.0);

  // Draw acceleration and rotation.
  gyro_0_accel.draw_lines({
    lines: [0, 1, 2].map(axis_i => measures.map(m => ({x: m.time - current_time, y: m.acceleration[axis_i]}))),
  });

  gyro_0_rot.draw_lines({
    lines: [0, 1, 2].map(axis_i => measures.map(m => ({x: m.time - current_time, y: m.rotation[axis_i]})))
  });
}


// Main
// ----

(async function() {
  await connected

  on("gyro-0-measure", add_measure);

  while (true) {
    await sleep(50);
    if (measures.length) {
      send("move-servo", {
        n: 1,
        position: _.clamp((_.last(measures).acceleration[1] / 9.8 + 1.0) / 2.0, 0.0, 1.0)
      });
    }
  }
}());


// Utils
// -----

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function gyro_inplace_weighted_average(last_measure, measure) {
  let total_duration = last_measure.duration + measure.duration;
  let {acceleration: last_accel} = last_measure;
  let {rotation: last_rot} = last_measure;
  let {acceleration: accel} = measure;
  let {rotation: rot} = measure;
  let {duration: last_w} = last_measure;
  let {duration: w} = measure;
  let total_w = total_duration;


  last_measure.duration = total_duration;
  last_measure.time = measure.time;
  for (let i of [0, 1, 2]) {
    last_measure.acceleration[i] = (last_accel[i] * last_w + accel[i] * w) / total_w;
    last_measure.rotation[i] = (last_rot[i] * last_w + rot[i] * w) / total_w;
  }
}

function fixed_width_float(x, {decimals=2, width=10}={}){
  return Number.parseFloat(x).toFixed(decimals).padStart(width)
}


