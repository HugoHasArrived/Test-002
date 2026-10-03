from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nightfall: Dead Ground</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            overflow: hidden;
            background: #020303;
            color: white;
            font-family: Arial, sans-serif;
        }

        canvas {
            display: block;
            background: #050707;
        }

        #menu {
            position: fixed;
            inset: 0;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            background:
                radial-gradient(circle at center, #17201b 0%, #060908 45%, #010202 100%);
        }

        #menu h1 {
            font-size: clamp(42px, 7vw, 90px);
            letter-spacing: 8px;
            margin: 0;
            color: #c9d2c5;
            text-shadow:
                0 0 10px #788f7c,
                0 0 35px #263d2c;
        }

        #menu p {
            color: #8d9890;
            letter-spacing: 4px;
            margin: 10px 0 35px;
        }

        button {
            padding: 15px 45px;
            background: #202c24;
            border: 1px solid #68776d;
            color: white;
            font-size: 18px;
            cursor: pointer;
            transition: .2s;
        }

        button:hover {
            background: #35483b;
            transform: scale(1.05);
        }

        #hud {
            display: none;
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 5;
        }

        #stats {
            position: absolute;
            top: 20px;
            left: 20px;
            width: 240px;
            padding: 15px;
            background: rgba(0,0,0,.55);
            border-left: 3px solid #788f7c;
        }

        .bar {
            height: 12px;
            background: #161918;
            margin: 6px 0 12px;
        }

        .fill {
            height: 100%;
            transition: width .15s;
        }

        #health {
            background: #a63d3d;
            width: 100%;
        }

        #stamina {
            background: #82967f;
            width: 100%;
        }

        #ammo {
            font-size: 20px;
        }

        #objective {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 15px;
            max-width: 300px;
            background: rgba(0,0,0,.55);
            color: #b8c5ba;
        }

        #message {
            position: absolute;
            bottom: 45px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 25px;
            background: rgba(0,0,0,.7);
            opacity: 0;
            transition: opacity .3s;
        }

        #crosshair {
            position: absolute;
            left: 50%;
            top: 50%;
            width: 20px;
            height: 20px;
            transform: translate(-50%,-50%);
        }

        #crosshair:before,
        #crosshair:after {
            content: "";
            position: absolute;
            background: rgba(255,255,255,.7);
        }

        #crosshair:before {
            width: 20px;
            height: 1px;
            top: 10px;
        }

        #crosshair:after {
            height: 20px;
            width: 1px;
            left: 10px;
        }

        #gameover {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 20;
            background: rgba(0,0,0,.9);
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }

        #gameover h2 {
            color: #a43b3b;
            font-size: 65px;
            letter-spacing: 8px;
        }

        #hint {
            position: absolute;
            bottom: 15px;
            left: 20px;
            color: #69736d;
            font-size: 13px;
        }
    </style>
</head>

<body>

<div id="menu">
    <h1>NIGHTFALL</h1>
    <p>DEAD GROUND</p>
    <button onclick="startGame()">ENTER THE DARKNESS</button>
    <div style="margin-top:25px;color:#59635d;font-size:13px;">
        WASD / ARROWS • SHIFT SPRINT • MOUSE AIM • CLICK SHOOT • E INTERACT
    </div>
</div>

<div id="hud">

    <div id="stats">
        HEALTH
        <div class="bar">
            <div id="health" class="fill"></div>
        </div>

        STAMINA
        <div class="bar">
            <div id="stamina" class="fill"></div>
        </div>

        <div id="ammo">AMMO: 12</div>
    </div>

    <div id="objective">
        <b>OBJECTIVE</b><br>
        Find the radio inside the abandoned bunker.
    </div>

    <div id="crosshair"></div>

    <div id="message"></div>

    <div id="hint">
        Find the bunker. Stay quiet. Something is hunting you.
    </div>
</div>

<div id="gameover">
    <h2>YOU DIED</h2>
    <p>The darkness found you.</p>
    <button onclick="location.reload()">TRY AGAIN</button>
</div>

<canvas id="game"></canvas>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

let W, H;

function resize() {
    W = canvas.width = innerWidth;
    H = canvas.height = innerHeight;
}

resize();
window.addEventListener("resize", resize);

const keys = {};

document.addEventListener("keydown", e => {
    keys[e.key.toLowerCase()] = true;

    if (e.key.toLowerCase() === "e") interact();
});

document.addEventListener("keyup", e => {
    keys[e.key.toLowerCase()] = false;
});

const mouse = {
    x: 0,
    y: 0,
    down: false
};

canvas.addEventListener("mousemove", e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

canvas.addEventListener("mousedown", () => {
    mouse.down = true;
});

canvas.addEventListener("mouseup", () => {
    mouse.down = false;
});

let player;
let enemies = [];
let bullets = [];
let buildings = [];
let items = [];

let gameRunning = false;
let ammo = 12;
let objectiveComplete = false;

function startGame() {

    document.getElementById("menu").style.display = "none";
    document.getElementById("hud").style.display = "block";

    player = {
        x: 500,
        y: 450,
        speed: 2.8,
        health: 100,
        stamina: 100,
        angle: 0
    };

    createWorld();
    gameRunning = true;

    requestAnimationFrame(loop);
}

function createWorld() {

    buildings = [
        {
            x: 180,
            y: 180,
            w: 300,
            h: 180,
            name: "Ruined House"
        },
        {
            x: 760,
            y: 120,
            w: 340,
            h: 210,
            name: "Bunker"
        },
        {
            x: 1250,
            y: 420,
            w: 350,
            h: 220,
            name: "Abandoned Factory"
        },
        {
            x: 400,
            y: 760,
            w: 450,
            h: 200,
            name: "Barracks"
        }
    ];

    items = [
        {
            x: 940,
            y: 220,
            type: "radio",
            collected: false
        },
        {
            x: 600,
            y: 650,
            type: "ammo",
            collected: false
        }
    ];

    enemies = [];

    for (let i = 0; i < 8; i++) {

        enemies.push({
            x: 200 + Math.random() * 1400,
            y: 150 + Math.random() * 850,
            speed: .45 + Math.random() * .35,
            health: 60,
            attackCooldown: 0,
            active: true
        });
    }
}

function update() {

    if (!player) return;

    let dx = 0;
    let dy = 0;

    if (keys["w"] || keys["arrowup"]) dy--;
    if (keys["s"] || keys["arrowdown"]) dy++;
    if (keys["a"] || keys["arrowleft"]) dx--;
    if (keys["d"] || keys["arrowright"]) dx++;

    let sprinting =
        keys["shift"] &&
        player.stamina > 0 &&
        (dx !== 0 || dy !== 0);

    let speed = sprinting ? 5 : player.speed;

    if (sprinting) {
        player.stamina -= .5;
    } else {
        player.stamina += .25;
    }

    player.stamina = Math.max(
        0,
        Math.min(100, player.stamina)
    );

    if (dx || dy) {

        let length = Math.sqrt(dx * dx + dy * dy);

        dx /= length;
        dy /= length;

        player.x += dx * speed;
        player.y += dy * speed;
    }

    player.angle = Math.atan2(
        mouse.y - H / 2,
        mouse.x - W / 2
    );

    updateEnemies();
    updateBullets();
    collectItems();

    if (mouse.down && ammo > 0) {
        shoot();
    }

    if (player.health <= 0) {
        gameOver();
    }
}

let shootCooldown = 0;

function shoot() {

    if (shootCooldown > 0) return;

    shootCooldown = 12;
    ammo--;

    bullets.push({
        x: player.x,
        y: player.y,
        dx: Math.cos(player.angle) * 10,
        dy: Math.sin(player.angle) * 10,
        life: 70
    });

    updateHUD();
}

function updateBullets() {

    shootCooldown--;

    for (let b of bullets) {

        b.x += b.dx;
        b.y += b.dy;
        b.life--;

        for (let e of enemies) {

            if (!e.active) continue;

            let d = Math.hypot(
                e.x - b.x,
                e.y - b.y
            );

            if (d < 25) {

                e.health -= 35;
                b.life = 0;

                if (e.health <= 0) {
                    e.active = false;
                    showMessage("Something stopped moving...");
                }
            }
        }
    }

    bullets = bullets.filter(b => b.life > 0);
}

function updateEnemies() {

    for (let e of enemies) {

        if (!e.active) continue;

        let dx = player.x - e.x;
        let dy = player.y - e.y;

        let distance = Math.hypot(dx, dy);

        if (distance < 650) {

            dx /= distance;
            dy /= distance;

            e.x += dx * e.speed;
            e.y += dy * e.speed;
        }

        if (distance < 35 && e.attackCooldown <= 0) {

            player.health -= 8;

            e.attackCooldown = 45;

            updateHUD();
        }

        e.attackCooldown--;
    }
}

function collectItems() {

    for (let item of items) {

        if (item.collected) continue;

        let d = Math.hypot(
            player.x - item.x,
            player.y - item.y
        );

        if (d < 40) {

            if (item.type === "ammo") {

                ammo += 12;
                item.collected = true;

                showMessage("You found ammunition.");

            }

            if (item.type === "radio") {

                objectiveComplete = true;
                item.collected = true;

                document.getElementById("objective").innerHTML =
                    "<b>OBJECTIVE COMPLETE</b><br>" +
                    "The radio crackles... someone answered.";

                showMessage(
                    "RADIO SIGNAL DETECTED"
                );
            }

            updateHUD();
        }
    }
}

function interact() {

    if (!player) return;

    for (let b of buildings) {

        if (
            player.x > b.x - 60 &&
            player.x < b.x + b.w + 60 &&
            player.y > b.y - 60 &&
            player.y < b.y + b.h + 60
        ) {

            showMessage(
                "The building is abandoned... but you hear footsteps."
            );

            return;
        }
    }
}

function showMessage(text) {

    const message =
        document.getElementById("message");

    message.textContent = text;
    message.style.opacity = 1;

    setTimeout(() => {
        message.style.opacity = 0;
    }, 2500);
}

function updateHUD() {

    document.getElementById("health").style.width =
        player.health + "%";

    document.getElementById("stamina").style.width =
        player.stamina + "%";

    document.getElementById("ammo").textContent =
        "AMMO: " + ammo;
}

function gameOver() {

    gameRunning = false;

    document.getElementById("hud").style.display =
        "none";

    document.getElementById("gameover").style.display =
        "flex";
}

function drawWorld() {

    ctx.fillStyle = "#101512";
    ctx.fillRect(0, 0, W, H);

    const cameraX = player.x - W / 2;
    const cameraY = player.y - H / 2;

    ctx.save();

    ctx.translate(-cameraX, -cameraY);

    // Ground

    ctx.fillStyle = "#182019";
    ctx.fillRect(
        -1000,
        -1000,
        3500,
        2500
    );

    // Ground details

    for (let i = 0; i < 250; i++) {

        let x = (i * 347) % 2400;
        let y = (i * 193) % 1600;

        ctx.fillStyle =
            i % 3 === 0
            ? "#1d281f"
            : "#121a15";

        ctx.fillRect(x, y, 8, 3);
    }

    // Roads

    ctx.fillStyle = "#252b28";

    ctx.fillRect(
        -100,
        500,
        2600,
        150
    );

    ctx.fillRect(
        1050,
        -100,
        160,
        1800
    );

    // Buildings

    for (let b of buildings) {

        ctx.fillStyle = "#262b28";
        ctx.fillRect(
            b.x,
            b.y,
            b.w,
            b.h
        );

        ctx.strokeStyle = "#4b534d";
        ctx.lineWidth = 5;

        ctx.strokeRect(
            b.x,
            b.y,
            b.w,
            b.h
        );

        // Windows

        for (
            let x = b.x + 35;
            x < b.x + b.w - 25;
            x += 65
        ) {

            ctx.fillStyle = "#111";
            ctx.fillRect(
                x,
                b.y + 35,
                35,
                35
            );
        }

        ctx.fillStyle = "#59635d";
        ctx.font = "14px Arial";

        ctx.fillText(
            b.name,
            b.x + 15,
            b.y + b.h - 15
        );
    }

    // Items

    for (let item of items) {

        if (item.collected) continue;

        ctx.beginPath();

        ctx.arc(
            item.x,
            item.y,
            12,
            0,
            Math.PI * 2
        );

        ctx.fillStyle =
            item.type === "radio"
            ? "#b4a85a"
            : "#7b8e7d";

        ctx.fill();

        ctx.shadowBlur = 15;
        ctx.shadowColor = "#ffffff";
        ctx.fill();

        ctx.shadowBlur = 0;
    }

    // Enemies

    for (let e of enemies) {

        if (!e.active) continue;

        ctx.save();

        ctx.translate(e.x, e.y);

        let angle =
            Math.atan2(
                player.y - e.y,
                player.x - e.x
            );

        ctx.rotate(angle);

        // body

        ctx.fillStyle = "#495047";

        ctx.beginPath();
        ctx.arc(0, 0, 17, 0, Math.PI * 2);
        ctx.fill();

        // head

        ctx.fillStyle = "#7d8278";

        ctx.beginPath();
        ctx.arc(14, 0, 10, 0, Math.PI * 2);
        ctx.fill();

        // eyes

        ctx.fillStyle = "#b33d3d";

        ctx.fillRect(19, -5, 3, 3);
        ctx.fillRect(19, 3, 3, 3);

        ctx.restore();
    }

    // Bullets

    ctx.fillStyle = "#e2d6a2";

    for (let b of bullets) {

        ctx.beginPath();

        ctx.arc(
            b.x,
            b.y,
            3,
            0,
            Math.PI * 2
        );

        ctx.fill();
    }

    // Player

    ctx.save();

    ctx.translate(
        player.x,
        player.y
    );

    ctx.rotate(player.angle);

    // body

    ctx.fillStyle = "#68786b";

    ctx.fillRect(
        -12,
        -13,
        25,
        27
    );

    // head

    ctx.fillStyle = "#c5a18a";

    ctx.beginPath();

    ctx.arc(
        10,
        0,
        11,
        0,
        Math.PI * 2
    );

    ctx.fill();

    // weapon

    ctx.fillStyle = "#171918";

    ctx.fillRect(
        12,
        -3,
        32,
        6
    );

    ctx.restore();

    ctx.restore();

    // Darkness / flashlight

    drawDarkness();
}

function drawDarkness() {

    const gradient =
        ctx.createRadialGradient(
            W / 2,
            H / 2,
            80,
            W / 2,
            H / 2,
            420
        );

    gradient.addColorStop(
        0,
        "rgba(0,0,0,0)"
    );

    gradient.addColorStop(
        .55,
        "rgba(0,0,0,.35)"
    );

    gradient.addColorStop(
        1,
        "rgba(0,0,0,.96)"
    );

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, W, H);
}

function loop() {

    if (!gameRunning) return;

    update();
    drawWorld();

    requestAnimationFrame(loop);
}
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
