/* =========================================================
   SHADERS — summer⇄interstellar cocktail. uCosmic (0..1)
   crossfades a hyper-real summer sky into a flower-power
   nebula + starfield, and recolors the pollen into stars.
   ========================================================= */

const NOISE = /* glsl */`
float hash13(vec3 p){ p=fract(p*0.1031); p+=dot(p,p.yzx+33.33); return fract((p.x+p.y)*p.z); }
float noise(vec3 x){
  vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(hash13(i+vec3(0,0,0)),hash13(i+vec3(1,0,0)),f.x),
                 mix(hash13(i+vec3(0,1,0)),hash13(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hash13(i+vec3(0,0,1)),hash13(i+vec3(1,0,1)),f.x),
                 mix(hash13(i+vec3(0,1,1)),hash13(i+vec3(1,1,1)),f.x),f.y), f.z);
}
float fbm(vec3 p){ float v=0.0,a=0.5; for(int i=0;i<5;i++){ v+=a*noise(p); p*=2.03; a*=0.5; } return v; }
`;

export const SKY = {
  vertex: /* glsl */`
    varying vec3 vDir;
    void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }
  `,
  fragment: /* glsl */`
    precision highp float;
    varying vec3 vDir;
    uniform float uTime; uniform float uCosmic; uniform vec3 uSun;
    ${NOISE}
    void main(){
      vec3 d = normalize(vDir);
      float h = clamp(d.y*0.5+0.5, 0.0, 1.0);
      vec3 horizon = vec3(1.00,0.80,0.58);
      vec3 mid     = vec3(0.62,0.78,0.98);
      vec3 zenith  = vec3(0.20,0.45,0.92);
      vec3 summer  = mix(horizon, mid, smoothstep(0.0,0.45,h));
      summer       = mix(summer, zenith, smoothstep(0.35,1.0,h));
      float sd  = max(dot(d, normalize(uSun)), 0.0);
      summer   += vec3(1.0,0.86,0.6) * pow(sd, 220.0) * 2.0;
      summer   += vec3(1.0,0.72,0.45) * pow(sd, 5.0) * 0.35;
      float clouds = smoothstep(0.45,0.95, fbm(d*2.2 + vec3(uTime*0.01,0.0,0.0)));
      summer = mix(summer, vec3(1.0,0.98,0.95), clouds*0.35*smoothstep(0.0,0.4,h));
      vec3 base = mix(vec3(0.02,0.02,0.06), vec3(0.05,0.03,0.12), h);
      float n1 = pow(fbm(d*2.6 + uTime*0.008), 2.2);
      float n2 = pow(fbm(d*4.5 + 12.0), 3.0);
      vec3 nebula = base;
      nebula += vec3(0.55,0.12,0.42) * n1;
      nebula += vec3(0.10,0.32,0.45) * n2;
      nebula += vec3(0.35,0.20,0.55) * pow(fbm(d*1.6+5.0),2.0) * 0.6;
      vec3 sp = d*320.0; vec3 cell=floor(sp);
      float hs = hash13(cell);
      float starMask = step(0.986, hs);
      float dist = length(fract(sp)-0.5);
      float star = starMask * smoothstep(0.5,0.05,dist);
      float tw = 0.6+0.4*sin(uTime*3.0 + hs*120.0);
      nebula += vec3(0.9,0.95,1.0) * star * tw;
      float hb = hash13(cell+7.0);
      nebula += vec3(1.0,0.8,0.6) * step(0.9975,hb) * smoothstep(0.5,0.0,dist) * (0.7+0.3*sin(uTime*2.0));
      vec3 col = mix(summer, nebula, uCosmic);
      col += (hash13(d*999.0+uTime)-0.5)/255.0;
      gl_FragColor = vec4(col, 1.0);
    }
  `,
};

export const POLLEN = {
  vertex: /* glsl */`
    attribute float aSeed; attribute float aSize; attribute vec3 aColor;
    varying float vSeed; varying vec3 vColor;
    uniform float uTime; uniform float uCosmic; uniform float uPix;
    void main(){
      vSeed = aSeed; vColor = aColor;
      vec3 p = position;
      float t = uTime*0.12 + aSeed*6.2831;
      float drift = 1.0 - uCosmic*0.85;
      p.x += sin(t)*2.4*drift;
      p.y += sin(t*0.7+aSeed)*1.2*drift;
      p.z += cos(t*0.9)*2.4*drift;
      vec4 mv = modelViewMatrix * vec4(p,1.0);
      float twinkle = mix(1.0, 0.55+0.45*sin(uTime*4.0+aSeed*30.0), uCosmic);
      gl_PointSize = aSize * uPix * (300.0/-mv.z) * twinkle;
      gl_Position = projectionMatrix * mv;
    }
  `,
  fragment: /* glsl */`
    precision highp float;
    varying float vSeed; varying vec3 vColor; uniform float uCosmic;
    void main(){
      vec2 uv = gl_PointCoord - 0.5; float d = length(uv);
      if(d>0.5) discard;
      float glow = pow(smoothstep(0.5,0.0,d), 1.6);
      vec3 warm = vColor;
      vec3 cold = mix(vColor, vec3(0.9,0.95,1.0), 0.7);
      gl_FragColor = vec4(mix(warm, cold, uCosmic), glow*mix(0.55,0.95,uCosmic));
    }
  `,
};
