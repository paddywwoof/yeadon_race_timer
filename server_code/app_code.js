//const YMAX = 53.86700;
//const YMIN = 53.87012;
const YMAX = 53.85600; // Y is lat so (lat, lon) => (y, x), reverse usual cartesian order
const YMIN = 53.85200;
const CANVAS_H = 800;
const CANVAS_OFFSET = [-1, 15]; // x, y NOT lat, lon! TODO find why needed
const YSCALE = CANVAS_H / (YMAX - YMIN);
//const XMAX = -1.67750;
//const XMIN = -1.67160;
const XMAX = -1.82900;
const XMIN = -1.83100;
const CANVAS_W = 800;
const XSCALE = YSCALE * Math.cos(53.867 * Math.PI / 180.0);
const LEG_DONE = 0.90;


// various global variable
let sketch, context_sketch;
let race_input, name_input, message, marks_input, marks, results;
let race; // string race id
let locations = {};
let mark_locs = [];
let min_time = Number.MAX_VALUE;
let x_click = 0;
let y_click = 0;
let offs_on = false; // offset draw point above touch
let canvas_top = 0; // set on mouse down, used for drawing position
let canvas_left = 0;
let number_marks = 0;
let mark_index = 0;

class Leg {
    // represents one leg of the race
    // attributes with default values
    size = 0.0;
    x_drctn = 1.0;
    y_drctn = 0.0;
    x_start = 0.0;
    y_start = 0.0;
    x_end = 1.0;
    y_end = 0.0;

    constructor(x_start, y_start, x_end, y_end) {
        this.x_start = x_start;
        this.y_start = y_start;
        this.x_end = x_end;
        this.y_end = y_end;
        const x_vec = x_end - x_start;
        const y_vec = y_end - y_start;
        this.size = Math.hypot(x_vec, y_vec);
        if (this.size != 0) {
            this.x_drctn = x_vec / this.size;
            this.y_drctn = y_vec / this.size;
        }
    }

    progress(x_posn, y_posn) {
        // return the progress of posn along the Leg from start (0.0) to end (1.0)
        const x_vec = x_posn - this.x_start;
        const y_vec = y_posn - this.y_start;
        const dot_prdct = x_vec * this.x_drctn + y_vec * this.y_drctn;
        if (dot_prdct < 0) {
            return 0;
        } else if (dot_prdct > this.size) {
            return 1.0;
        } else {
            return dot_prdct / this.size;
        }
    }
}

function gameStart() {
    sketch = document.getElementById('sketch');
    race_input = document.getElementById('race');
    message = document.getElementById('message');
    context_sketch = sketch.getContext('2d');
    sketch.addEventListener('mousedown', mouseDown);
    marks_input = document.getElementById('number_marks');
    marks = document.getElementById('marks');
    results = document.getElementById('results');
}

//
// various drawing functions
//
function drawArray(arr, colour, closed=false) {
    // uses global context_sketch. arr in form [[tm, lat, lon], ...]
    context_sketch.beginPath();
    context_sketch.strokeStyle = colour;
    context_sketch.lineWidth = 2;
    context_sketch.moveTo(arr[0][2], arr[0][1]); lon => x, lat => y
    arr.slice(1).forEach(point => {
        context_sketch.lineTo(point[2], point[1]);
    });
    if (closed) {
        context_sketch.lineTo(arr[0][2], arr[0][1]);
    }
    context_sketch.stroke();
}

function drawMark(i) {
    const x = mark_locs[i][2];
    const y = mark_locs[i][1]
    context_sketch.beginPath();
    context_sketch.strokeStyle = "black";
    context_sketch.font = "25px sans";
    context_sketch.fillText(String.fromCharCode(65 + i), x, y);
    context_sketch.stroke();
    drawArray([
        [0, y - 3, x - 3],
        [0, y - 3, x + 3],
        [0, y + 3, x + 3],
        [0, y + 3, x - 3],
        [0, y - 3, x - 3]
    ], "green");

}

function redrawLocations() {
    const colours = ["red", "yellow", "green", "orange", "blue", "white", "purple", "pink"];
    let colour_ix = 0;
    Object.keys(locations).forEach(key => {
        drawArray(locations[key], colours[colour_ix]);
        colour_ix += 1;
        if (colour_ix >= colours.length) {
            colour_ix = 0;
        }
    });
}

function getXY(e) {
    let new_x = e.offsetX;
    let new_y = e.offsetY;
    let offs = 16;
    if (new_x === undefined && e.touches.length > 0) { // touch device
        let touch = e.touches[0];
        new_x = touch.pageX - canvas_left;
        new_y = touch.pageY - canvas_top;
        offs = offs_on ? 52 : 0;
    }
    return [Math.round(new_x), Math.round(new_y - offs)]
}

function mouseDown(e) {
    const rect = sketch.getBoundingClientRect();
    canvas_top = rect.top; // relies on the screen not scrolling poss TODO
    canvas_left = rect.left;
    let [new_x, new_y] = getXY(e);
    x_click = new_x + CANVAS_OFFSET[0];
    y_click = new_y + CANVAS_OFFSET[1];
    mark_locs[mark_index] = [0, y_click, x_click]; // unused tm and order as lat, lon so drawArray() can be used
    drawMark(mark_index);
    e.preventDefault();
    redraw();
}

function redraw() {
    if (mark_locs.length > 2 && !mark_locs.includes(undefined)) {
        context_sketch.clearRect(0, 0, sketch.width, sketch.height);
        drawArray(mark_locs, "black", true);
        for (let i = 0; i < mark_locs.length; i++) {
            drawMark(i);
        }
    }
    redrawLocations();
    results_html = "";
    const dist_times = calcDistances();
    Object.keys(dist_times).forEach(key => {
        const std_tm = (dist_times[key].speed != 0) ? 100.0 / dist_times[key].speed : 0.0;
        const std_h = Math.floor(std_tm);
        const std_m = Math.floor((std_tm - std_h) * 60.0);
        const std_s = Math.floor((std_tm - std_h - std_m / 60.0) * 3600.0);

        results_html += `${key} => legs:${dist_times[key].legs},  distance:${dist_times[key].distance.toFixed(1)},  speed:${dist_times[key].speed.toFixed(1)},  std_tm:${std_h}:${std_m}:${std_s}<br />`
    });
    results.innerHTML = results_html;
}

function enterRace() {
    race_input = document.getElementById('race');
    race = race_input.value.trim();
    if (race.match(/^[0-9]{6}-[0-9]{4}$/g)) {
        getResults();
    }
}

function getResults() {
    fetch('yeadon_query_data.php',
        {method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            race: race,
        })}
    )
    .then((response) => {
        //console.log(response);
        return response.json();
    })
    .then((responseJson) => {
        //console.log(responseJson);
        let num_loaded = 0;
        if (responseJson.status > 0) { // got sql response
            num_loaded = responseJson.results.length;
            if (responseJson.results.length > 0) { // more than zero names
                locations = {}; // will become {'uid0': [[tm, lat, lon], [..]..], 'uid1':[[..]..]] }
                min_time = Number.MAX_VALUE;
                min_lat = Number.MAX_VALUE;
                max_lat = -Number.MAX_VALUE;
                min_lon = Number.MAX_VALUE;
                max_lon = -Number.MAX_VALUE;
                responseJson.results.forEach((val) => {
                    const newrec = [val[1], val[2], val[3]]; // time, lat, lon
                    if (val[1] < min_time) {min_time = val[1];}
                    if (val[2] < min_lat) {min_lat = val[2];}
                    if (val[2] > max_lat) {max_lat = val[2];}
                    if (val[3] < min_lon) {min_lon = val[3];}
                    if (val[3] > max_lon) {max_lon = val[3];}
                    if (val[0] in locations) { // uid
                        locations[val[0]].push(newrec);
                    } else {
                        locations[val[0]] = [newrec];
                    }
                });
                Object.values(locations).forEach(values => {
                    values.forEach(point => {
                        point[0] -= min_time;
                        point[1] = CANVAS_H - (point[1] - YMIN) * YSCALE + CANVAS_OFFSET[1]; // lat NB (tm, lat, lon) reverse cartesian convension (tm, x, y)
                        point[2] = (point[2] - XMIN) * XSCALE + CANVAS_OFFSET[0]; // lon
                    });
                });
            }
            message.innerHTML = `loaded ${num_loaded} locations via API ${min_lat}..${max_lat} ${min_lon}..${max_lon}`;
            redraw();
        } else {
            message.innerHTML = "error checking server";
        }
    })
    .catch((error) =>{
        message.innerHTML = error;
    });
}

function redrawButtons() {
    // run when number of marks changed
    number_marks = marks_input.value;
    mark_locs.length = number_marks; // could have unfilled slots (null values)
    let marks_html = "";
    for (let i = 0; i < number_marks; i++){
        marks_html += `<button onclick="setMarkIndex(${i})" id="mark_btn${i}">Set Position of Mark ${String.fromCharCode(65 + i)}</button><br />`;
    }
    marks.innerHTML = marks_html;
}

function setMarkIndex(i) {
    mark_index = i;
}

function calcDistances() {
    if (mark_locs.length < 3 || mark_locs.includes(undefined)) {
        return {}; // empty object until there are three mark locations
    }
    let distances = {};
    Object.keys(locations).forEach(key => {
        let mk_fr = 0;
        let mk_to = 1;
        let completed_dist = 0;
        let completed_num = 0;
        let incomplete_leg = 0;
        let this_leg = new Leg(mark_locs[mk_fr][2], mark_locs[mk_fr][1], mark_locs[mk_to][2], mark_locs[mk_to][1]);
        Object.values(locations[key]).forEach(val => {
            incomplete_leg = this_leg.progress(val[2], val[1]); // val is [tm, lat, lon]
            if (incomplete_leg > LEG_DONE) {
                // at mark! TODO actual threshold. Also, should next Leg be near to unstarted?
                // should there be additional Math.hypot(val[2] - this_leg.x_end, val[1] - this_leg.y_end) < ROUNDING_DIST?
                completed_dist += this_leg.size;
                completed_num += 1;
                incomplete_leg = 0;
                mk_fr = mk_to;
                mk_to += 1;
                if (mk_to >= mark_locs.length) {
                    mk_to = 0;
                }
                this_leg = new Leg(mark_locs[mk_fr][2], mark_locs[mk_fr][1], mark_locs[mk_to][2], mark_locs[mk_to][1]);
            }
        });
        const tm = locations[key].slice(-1)[0][0] - locations[key][0][0]; // last location time - first location time.
        distances[key] = {"distance": (completed_dist + incomplete_leg), "speed": (completed_dist + incomplete_leg) * 60.0 / tm, "legs": completed_num};
    });
    return distances;
}