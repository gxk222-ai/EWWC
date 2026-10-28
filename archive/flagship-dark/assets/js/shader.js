/* Hero backdrop: a single fragment shader (slow champagne light sweep over brushed obsidian, fine grain).
   Stands in for the cinematic film until footage is available. Pauses off-screen and when the tab is hidden. */
(function () {
  var canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  var gl = canvas.getContext('webgl', { antialias: false, alpha: false, powerPreference: 'low-power' });
  if (!gl) return; // CSS gradient on .hero remains as fallback

  var vert = 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  var frag = [
    'precision mediump float;',
    'uniform vec2 r;uniform float t;',
    'float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}',
    'float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);',
    ' return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}',
    'float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p*=2.02;a*=.5;}return v;}',
    'void main(){',
    ' vec2 uv=gl_FragCoord.xy/r;vec2 q=uv;q.x*=r.x/r.y;',
    ' float tt=t*.035;',
    ' float f=fbm(q*1.6+vec2(tt,-tt*.6));',
    ' float g=fbm(q*3.2+f*1.4-vec2(tt*.8,0.));',
    // brushed-metal streaks
    ' float streak=fbm(vec2(q.x*0.6,q.y*38.)+tt*.4)*.08;',
    // diagonal light sweep
    ' float sweep=smoothstep(.55,0.,abs(q.x*.55-q.y+.15-sin(tt*1.3)*.35));',
    ' float light=pow(g,2.2)*sweep*1.25+streak*sweep;',
    ' vec3 base=vec3(.027,.027,.039);',
    ' vec3 champ=vec3(.784,.663,.494);',
    ' vec3 col=base+champ*light*.55;',
    // fine line network hint
    ' float lines=smoothstep(.985,1.,sin((q.x+q.y*.35+f*.4)*90.))*.04*sweep;',
    ' col+=champ*lines;',
    ' col*=1.-.55*length(uv-vec2(.65,.6));',
    ' col+=(h(gl_FragCoord.xy+t)-.5)*.035;',
    ' gl_FragColor=vec4(col,1.);}'
  ].join('\n');

  function sh(type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn(gl.getShaderInfoLog(s)); return null; }
    return s;
  }
  var vs = sh(gl.VERTEX_SHADER, vert), fs = sh(gl.FRAGMENT_SHADER, frag);
  if (!vs || !fs) return;
  var prog = gl.createProgram();
  gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
  gl.useProgram(prog);

  var buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(prog, 'p');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  var uR = gl.getUniformLocation(prog, 'r'), uT = gl.getUniformLocation(prog, 't');

  // Render at reduced resolution: the image is soft by design, and this keeps the GPU cost low.
  var scale = 0.5;
  function resize() {
    var w = Math.max(1, Math.floor(canvas.clientWidth * scale));
    var h = Math.max(1, Math.floor(canvas.clientHeight * scale));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; gl.viewport(0, 0, w, h); }
    gl.uniform2f(uR, w, h);
  }

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var visible = true, running = false, start = performance.now(), offset = 20;

  function draw(now) {
    resize();
    gl.uniform1f(uT, offset + (now - start) / 1000);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  function loop(now) {
    if (!running) return;
    draw(now);
    requestAnimationFrame(loop);
  }
  function update() {
    var should = visible && !document.hidden && !reduce.matches && !document.documentElement.classList.contains('reduce-motion');
    if (should && !running) { running = true; requestAnimationFrame(loop); }
    else if (!should) { running = false; draw(performance.now()); }
  }

  new IntersectionObserver(function (e) { visible = e[0].isIntersecting; update(); }).observe(canvas);
  document.addEventListener('visibilitychange', update);
  reduce.addEventListener && reduce.addEventListener('change', update);
  window.addEventListener('resize', function () { if (!running) draw(performance.now()); });
  window.__heroShaderUpdate = update;
  draw(performance.now());
  update();
})();
