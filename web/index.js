import "./style.css"

import _ from "lodash"
import * as d3 from "d3"


import {Plot} from "./plot.js"
import {GyroPlot} from "./gyro_plot.js"
import {ServoControls} from "./servo_controls.js"

import { SSL_OP_EPHEMERAL_RSA } from "constants";

// PI Connection
// -------------

const socket = new WebSocket("ws://192.168.1.8:45223");

const connected = new Promise(function(resolve, reject){
  socket.onopen = resolve
  socket.onerror = reject
})

const send = (event, data) => socket.send(JSON.stringify([event, data]))

const dispatcher = d3.dispatch("time", "gyro-0-measure", "servo-position");

socket.onmessage = (message) => {
  const [received_event, received_data] = JSON.parse(message.data);
  dispatcher.call(received_event, socket, received_data);
}

const on = (event, callback) => {
  send("subscribe", event.split(".")[0]);
  dispatcher.on(event, callback);
}

// Plotting & Controls
// -------------------

let gyro_plot = new GyroPlot("#gyro-0", "Gyro 0");
let servo_controls = new ServoControls("#servos", "Servo", send);


// Main
// ----

async function main() {
  await connected;

  on("gyro-0-measure", measure => gyro_plot.add_measure(measure));
  on("servo-position", position => servo_controls.add_position(position));
  on("time.servo", time => servo_controls.update_time(time));

}

main();


// Utils
// -----

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


function str_float(x, {decimals=2, width=10}={}){
  return Number.parseFloat(x).toFixed(decimals).padStart(width)
}
