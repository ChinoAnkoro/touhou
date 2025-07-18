const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// プレイヤーの初期設定
const player = {
    x: canvas.width / 2 - 25,
    y: canvas.height - 60,
    width: 50,
    height: 50,
    speed: 5,
    dx: 0,
    dy: 0,
    // アイテム効果
    life: 3,
    shotType: 'normal',
    bulletPower: 1,
    bulletSize: 5,
    hasBarrier: false,
    specialAttackStock: 2
};

// ゲームの状態
let score = 0;
let gameLoopId; // ゲームループのID
let gamePhase = 'stage'; // stage, boss, gameover, clear
let enemySpawner; // 敵の出現タイマー
let cloudSpawner; // 雲の出現タイマー

// キー入力
const keys = {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
    ' ': false,
    'z': false,
    'x': false
};

// アイテムの定義
const itemTypes = [
    { name: 'score', color: 'yellow' },
    { name: 'speed', color: 'blue' },
    { name: 'power', color: 'grey' },
    { name: '3way', color: 'purple' },
    { name: 'barrier', color: 'pink' },
    { name: 'bomb', color: 'white' } // 点滅
];

// プレイヤーの状態
const playerState = {
    isHammering: false,
    hammerCooldown: 10,
    hammerTimer: 0
};

// ハンマーの定義
const hammer = {
    width: 70,
    height: 70,
    damage: 5
};

// 配列
const bullets = [];
const enemies = [];
const enemyBullets = [];
const clouds = [];
const items = [];
const healItems = []; // 回復アイテム配列

// ボスの定義
let boss = null;

document.addEventListener('keydown', (e) => {
    const key = e.key.toLowerCase();
    if (gamePhase === 'gameover' || gamePhase === 'clear') return;
    if (key in keys) keys[key] = true;
    if (key === ' ') createBullet();
    if (key === 'z') triggerHammer();
    if (key === 'x') triggerSpecialAttack();
});
document.addEventListener('keyup', (e) => {
    const key = e.key.toLowerCase();
    if (key in keys) keys[key] = false;
});

// 描画：プレイヤー
function drawPlayer() {
    // バリアの描画
    if (player.hasBarrier) {
        ctx.fillStyle = 'rgba(0, 150, 255, 0.4)';
        ctx.beginPath();
        ctx.arc(player.x + player.width / 2, player.y + player.height / 2, player.width, 0, Math.PI * 2);
        ctx.fill();
    }
    // 本体
    ctx.fillStyle = 'white';
    ctx.fillRect(player.x, player.y, player.width, player.height);
}

// 移動：プレイヤー
function movePlayer() {
    player.dx = 0;
    player.dy = 0;
    if (keys.ArrowUp) player.dy = -player.speed;
    if (keys.ArrowDown) player.dy = player.speed;
    if (keys.ArrowLeft) player.dx = -player.speed;
    if (keys.ArrowRight) player.dx = player.speed;

    player.x += player.dx;
    player.y += player.dy;

    if (player.x < 0) player.x = 0;
    if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;
    if (player.y < 0) player.y = 0;
    if (player.y + player.height > canvas.height) player.y = canvas.height - player.height;
}

// --- 攻撃関連 --- 

function triggerHammer() {
    if (playerState.hammerTimer <= 0) {
        playerState.isHammering = true;
        playerState.hammerTimer = playerState.hammerCooldown;
    }
}

function handleHammer() {
    if (playerState.hammerTimer > 0) {
        playerState.hammerTimer--;
    } else {
        playerState.isHammering = false;
    }

    if (playerState.isHammering) {
        ctx.fillStyle = 'rgba(255, 255, 100, 0.5)';
        ctx.fillRect(
            player.x + player.width / 2 - hammer.width / 2,
            player.y - hammer.height / 2,
            hammer.width,
            hammer.height
        );
    }
}

function createBullet() {
    const bulletProps = {
        y: player.y,
        width: player.bulletSize,
        height: player.bulletSize * 2,
        speed: 8,
        power: player.bulletPower,
        color: 'yellow'
    };

    if (player.shotType === '3way') {
        bullets.push({ ...bulletProps, x: player.x + player.width / 2 - bulletProps.width / 2, dx: 0 });
        bullets.push({ ...bulletProps, x: player.x, dx: -1 });
        bullets.push({ ...bulletProps, x: player.x + player.width - bulletProps.width, dx: 1 });
    } else {
        bullets.push({ ...bulletProps, x: player.x + player.width / 2 - bulletProps.width / 2, dx: 0 });
    }
}

function handleBullets() {
    for (let i = bullets.length - 1; i >= 0; i--) {
        const b = bullets[i];
        b.y -= b.speed;
        b.x += b.dx * (b.speed / 2); // 3way
        if (b.y < 0) {
            bullets.splice(i, 1);
        } else {
            ctx.fillStyle = b.color;
            ctx.fillRect(b.x, b.y, b.width, b.height);
        }
    }
}

// --- 敵関連 --- 

function spawnEnemy() {
    const type = Math.random();
    if (type < 0.6) createShooterEnemy();
    else if (type < 0.85) createSwarmerEnemy();
    else createArmoredEnemy();
}

function createShooterEnemy() {
    const size = 40;
    enemies.push({ type: 'shooter', x: Math.random() * (canvas.width - size), y: -size, width: size, height: size, speed: 2, color: 'red', health: 2 });
}

function createSwarmerEnemy() {
    const size = 20;
    enemies.push({ type: 'swarmer', x: Math.random() * (canvas.width - size), y: -size, width: size, height: size, speed: 4, color: 'orange', health: 1 });
}

function createArmoredEnemy() {
    const size = 50;
    enemies.push({ type: 'armored', x: Math.random() * (canvas.width - size), y: -size, width: size, height: size, speed: 1, color: 'grey', health: 5 });
}

function handleEnemies() {
    for (let i = enemies.length - 1; i >= 0; i--) {
        const e = enemies[i];
        e.y += e.speed;
        if (e.y > canvas.height) {
            enemies.splice(i, 1);
        } else {
            ctx.fillStyle = e.color;
            ctx.fillRect(e.x, e.y, e.width, e.height);
            if (e.type === 'shooter' && Math.random() < 0.02) {
                createEnemyBullet(e, Math.PI / 2);
            }
        }
    }
}

function createEnemyBullet(source, angle) {
    enemyBullets.push({ 
        x: source.x + source.width / 2 - 2.5, 
        y: source.y + source.height / 2, 
        width: 5, height: 10, 
        speed: 4, 
        color: 'pink',
        dx: Math.cos(angle) * 4,
        dy: Math.sin(angle) * 4
    });
}

function handleEnemyBullets() {
    for (let i = enemyBullets.length - 1; i >= 0; i--) {
        const b = enemyBullets[i];
        b.x += b.dx;
        b.y += b.dy;
        if (b.y > canvas.height || b.y < 0 || b.x < 0 || b.x > canvas.width) {
            enemyBullets.splice(i, 1);
        } else {
            ctx.fillStyle = b.color;
            ctx.fillRect(b.x, b.y, b.width, b.height);
        }
    }
}

// --- 雲とアイテム ---

function spawnCloud() {
    const side = Math.random() < 0.5 ? 'left' : 'right';
    clouds.push({ x: side === 'left' ? -120 : canvas.width, y: Math.random() * (canvas.height / 4), width: 120, height: 60, speed: side === 'left' ? 1 : -1, droppedItem: false });
}

function handleClouds() {
    for (let i = clouds.length - 1; i >= 0; i--) {
        const c = clouds[i];
        c.x += c.speed;
        if (!c.droppedItem && Math.abs(c.x + c.width / 2 - canvas.width / 2) < 20) {
            c.droppedItem = true;
            createItem(c);
        }
        if (c.x > canvas.width || c.x < -c.width) {
            clouds.splice(i, 1);
        } else {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.beginPath();
            ctx.ellipse(c.x + c.width / 2, c.y + c.height / 2, c.width / 2, c.height / 2, 0, 0, 2 * Math.PI);
            ctx.fill();
        }
    }
}

function createItem(cloud) {
    items.push({ x: cloud.x + cloud.width / 2 - 10, y: cloud.y + cloud.height, width: 20, height: 20, speed: 1.5, typeIndex: 0, get type() { return itemTypes[this.typeIndex]; } });
}

function handleItems() {
    for (let i = items.length - 1; i >= 0; i--) {
        const item = items[i];
        item.y += item.speed;
        if (item.y > canvas.height) {
            items.splice(i, 1);
        } else {
            if (item.type.name === 'bomb') {
                ctx.fillStyle = `rgba(255, 255, 255, ${Math.abs(Math.sin(Date.now() / 100))})`;
            } else {
                ctx.fillStyle = item.type.color;
            }
            ctx.fillRect(item.x, item.y, item.width, item.height);
        }
    }
}

function createHealItem(enemy) {
    healItems.push({ 
        x: enemy.x + enemy.width / 2 - 10,
        y: enemy.y + enemy.height / 2 - 10,
        width: 20, height: 20, speed: 2, color: 'lime'
    });
}

function handleHealItems() {
    for (let i = healItems.length - 1; i >= 0; i--) {
        const item = healItems[i];
        item.y += item.speed;
        if (item.y > canvas.height) {
            healItems.splice(i, 1);
        } else {
            ctx.fillStyle = item.color;
            ctx.fillRect(item.x, item.y, item.width, item.height);
        }
    }
}

// --- ボス関連 --- 

function createBoss() {
    boss = {
        x: canvas.width / 2 - 100,
        y: -200,
        width: 200,
        height: 200,
        speed: 1,
        dx: 1,
        health: 500,
        maxHealth: 500,
        color: 'purple',
        attackPattern: 'descend',
        attackTimer: 0
    };
}

function handleBoss() {
    if (!boss) return;

    switch (boss.attackPattern) {
        case 'descend':
            boss.y += boss.speed;
            if (boss.y >= 50) {
                boss.attackPattern = 'barrage';
            }
            break;
        case 'barrage':
            boss.x += boss.dx * boss.speed;
            if (boss.x <= 0 || boss.x + boss.width >= canvas.width) {
                boss.dx *= -1;
            }
            boss.attackTimer++;
            if (boss.attackTimer % 20 === 0) {
                for (let i = 0; i < 8; i++) {
                    const angle = (Math.PI * 2 / 8) * i + (boss.attackTimer / 50);
                    createEnemyBullet(boss, angle);
                }
            }
            break;
    }

    ctx.fillStyle = boss.color;
    ctx.fillRect(boss.x, boss.y, boss.width, boss.height);

    ctx.fillStyle = 'red';
    ctx.fillRect(boss.x, boss.y - 20, boss.width, 10);
    ctx.fillStyle = 'green';
    ctx.fillRect(boss.x, boss.y - 20, boss.width * (boss.health / boss.maxHealth), 10);
}


// --- システム --- 

function checkCollisions() {
    // プレイヤーの弾 vs 敵
    for (let i = bullets.length - 1; i >= 0; i--) {
        for (let j = enemies.length - 1; j >= 0; j--) {
            const bullet = bullets[i];
            const enemy = enemies[j];
            if (bullet && enemy && isColliding(bullet, enemy)) {
                if (enemy.type === 'armored') {
                    bullets.splice(i, 1);
                    continue;
                }
                enemy.health -= bullet.power;
                bullets.splice(i, 1);
                if (enemy.health <= 0) {
                    enemies.splice(j, 1);
                    score += 100;
                    if (Math.random() < 0.1) {
                        createHealItem(enemy);
                    }
                }
                break;
            }
        }
    }

    // ハンマー vs 敵
    if (playerState.isHammering) {
        const hammerHitbox = { x: player.x + player.width / 2 - hammer.width / 2, y: player.y - hammer.height / 2, width: hammer.width, height: hammer.height };
        for (let j = enemies.length - 1; j >= 0; j--) {
            const enemy = enemies[j];
            if (enemy && isColliding(hammerHitbox, enemy)) {
                enemy.health -= hammer.damage;
                if (enemy.health <= 0) {
                    enemies.splice(j, 1);
                    score += 150;
                    if (Math.random() < 0.1) {
                        createHealItem(enemy);
                    }
                }
            }
        }
    }

    // プレイヤーの弾 vs アイテム
    for (let i = bullets.length - 1; i >= 0; i--) {
        for (let j = items.length - 1; j >= 0; j--) {
            const bullet = bullets[i];
            const item = items[j];
            if (bullet && item && isColliding(bullet, item)) {
                bullets.splice(i, 1);
                item.typeIndex = (item.typeIndex + 1) % itemTypes.length;
                break;
            }
        }
    }

    // プレイヤー vs アイテム
    for (let i = items.length - 1; i >= 0; i--) {
        const item = items[i];
        if (item && isColliding(player, item)) {
            applyItemEffect(item.type);
            items.splice(i, 1);
        }
    }

    // プレイヤー vs 回復アイテム
    for (let i = healItems.length - 1; i >= 0; i--) {
        const item = healItems[i];
        if (item && isColliding(player, item)) {
            player.life = Math.min(player.life + 1, 5);
            healItems.splice(i, 1);
        }
    }

    // 敵の弾 vs プレイヤー
    for (let i = enemyBullets.length - 1; i >= 0; i--) {
        if (isColliding(enemyBullets[i], player)) {
            enemyBullets.splice(i, 1);
            if (player.hasBarrier) {
                player.hasBarrier = false;
            } else {
                player.life--;
                if (player.life <= 0) {
                    gameOver();
                }
            }
            return;
        }
    }
}

function checkBossCollisions() {
    if (!boss) return;
    const hammerHitbox = { x: player.x + player.width / 2 - hammer.width / 2, y: player.y - hammer.height / 2, width: hammer.width, height: hammer.height };

    for (let i = bullets.length - 1; i >= 0; i--) {
        if (isColliding(bullets[i], boss)) {
            boss.health -= bullets[i].power;
            bullets.splice(i, 1);
        }
    }

    if (playerState.isHammering && isColliding(hammerHitbox, boss)) {
        boss.health -= hammer.damage;
    }

    if (boss.health <= 0) {
        gameClear();
    }
}

function applyItemEffect(type) {
    switch (type.name) {
        case 'score':
            score += 1000;
            break;
        case 'speed':
            player.speed = Math.min(player.speed + 1, 10);
            break;
        case 'power':
            player.shotType = 'normal';
            player.bulletPower = Math.min(player.bulletPower + 1, 5);
            player.bulletSize = Math.min(player.bulletSize + 2, 15);
            break;
        case '3way':
            player.shotType = '3way';
            player.bulletPower = 1;
            player.bulletSize = 5;
            break;
        case 'barrier':
            player.hasBarrier = true;
            break;
        case 'bomb':
            player.specialAttackStock = Math.min(player.specialAttackStock + 1, 5);
            break;
    }
}

function isColliding(a, b) {
    return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

function drawUI() {
    ctx.fillStyle = 'white';
    ctx.font = '24px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`Score: ${score}`, 10, 30);
    ctx.fillText(`Life: ${player.life}`, 10, 60);
    ctx.fillText(`Bomb: ${player.specialAttackStock}`, 10, 90);
}

function triggerSpecialAttack() {
    if (player.specialAttackStock > 0) {
        player.specialAttackStock--;
        enemyBullets.length = 0;
        for (const enemy of enemies) {
            enemy.health -= 10;
        }
        if (boss) {
            boss.health -= 50;
        }
    }
}

function gameOver() {
    if (gamePhase !== 'gameover') {
        gamePhase = 'gameover';
        cancelAnimationFrame(gameLoopId);
        clearInterval(enemySpawner);
        clearInterval(cloudSpawner);
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'white';
        ctx.font = '60px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', canvas.width / 2, canvas.height / 2);
    }
}

function gameClear() {
    if (gamePhase !== 'clear') {
        gamePhase = 'clear';
        cancelAnimationFrame(gameLoopId);
        clearInterval(enemySpawner);
        clearInterval(cloudSpawner);
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'gold';
        ctx.font = '60px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('GAME CLEAR', canvas.width / 2, canvas.height / 2);
    }
}

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// --- メインループ ---
function gameLoop() {
    clearCanvas();

    if (gamePhase === 'stage' && score >= 5000) {
        gamePhase = 'boss';
        clearInterval(enemySpawner);
        enemies.length = 0;
        createBoss();
    }
    
    movePlayer();
    drawPlayer();

    handleHammer();
    handleBullets();
    handleItems();
    handleHealItems();

    if (gamePhase === 'stage') {
        handleEnemies();
        handleClouds();
    } else if (gamePhase === 'boss') {
        handleBoss();
        checkBossCollisions();
    }
    
    handleEnemyBullets();

    checkCollisions();
    drawUI();

    gameLoopId = requestAnimationFrame(gameLoop);
}

// --- ゲーム開始 ---
function startGame() {
    enemySpawner = setInterval(spawnEnemy, 1000);
    cloudSpawner = setInterval(spawnCloud, 8000);
    gameLoop();
}

startGame();