// NEXUS HOTEL - Unified Aurora Background (Dark + Light)
(function() {
    const canvas = document.getElementById('auroraCanvas');
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 768 ? 1 : 2));

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const uniforms = {
        uTime: { value: 0 },
        uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
        uMouse: { value: new THREE.Vector2(0.5, 0.5) },
        uIsDark: { value: 1.0 },
    };

    const vertexShader = `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position, 1.0); }`;

    const fragmentShader = `
        precision highp float;
        uniform float uTime;
        uniform vec2 uResolution;
        uniform vec2 uMouse;
        uniform float uIsDark;
        varying vec2 vUv;

        vec3 mod289(vec3 x){return x-floor(x/289.0)*289.0;}
        vec2 mod289(vec2 x){return x-floor(x/289.0)*289.0;}
        vec3 permute(vec3 x){return mod289((x*34.0+1.0)*x);}

        float snoise(vec2 v){
            const vec4 C=vec4(0.211324865,0.366025403,-0.577350269,0.024390243);
            vec2 i=floor(v+dot(v,C.yy));
            vec2 x0=v-i+dot(i,C.xx);
            vec2 i1=(x0.x>x0.y)?vec2(1.0,0.0):vec2(0.0,1.0);
            vec4 x12=x0.xyxy+C.xxzz; x12.xy-=i1;
            i=mod289(i);
            vec3 p=permute(permute(i.y+vec3(0.0,i1.y,1.0))+i.x+vec3(0.0,i1.x,1.0));
            vec3 m=max(0.5-vec3(dot(x0,x0),dot(x12.xy,x12.xy),dot(x12.zw,x12.zw)),0.0);
            m=m*m; m=m*m;
            vec3 x=2.0*fract(p*C.www)-1.0;
            vec3 h=abs(x)-0.5;
            vec3 ox=floor(x+0.5);
            vec3 a0=x-ox;
            m*=1.79284291400159-0.85373472095314*(a0*a0+h*h);
            vec3 g; g.x=a0.x*x0.x+h.x*x0.y; g.yz=a0.yz*x12.xz+h.yz*x12.yw;
            return 130.0*dot(m,g);
        }

        float fbm(vec2 p){
            float f=0.0, w=0.5;
            for(int i=0;i<4;i++){f+=w*snoise(p);p*=2.0;w*=0.5;}
            return f;
        }

        float fbm3(vec2 p){
            vec2 q=vec2(fbm(p),fbm(p+vec2(5.2,1.3)));
            return fbm(p+4.0*q+vec2(1.7,9.2)+0.1*uTime*0.12);
        }

        void main(){
            vec2 uv=gl_FragCoord.xy/uResolution;
            float aspect=uResolution.x/uResolution.y;
            vec2 p=uv; p.x*=aspect;
            float t=uTime*0.15;
            float dark=uIsDark;

            // Base color: dark or light
            vec3 darkBase=vec3(0.01,0.015,0.04);
            vec3 lightBase=vec3(0.86,0.88,0.92);
            vec3 col=mix(lightBase, darkBase, dark);

            // Stars (dark only)
            float s1=snoise(uv*400.0)*snoise(uv*200.0+100.0);
            s1=smoothstep(0.35,0.4,s1)*0.5;
            float s2=snoise(uv*600.0+50.0)*snoise(uv*300.0+200.0);
            s2=smoothstep(0.4,0.44,s2)*0.3;
            col+=(s1+s2)*vec3(0.75,0.85,1.0)*dark;

            // Aurora layers
            float speedMul=mix(0.7, 1.0, dark);
            float brightMul=mix(0.55, 1.0, dark);

            for(int i=0;i<5;i++){
                float fi=float(i);
                float speed=(0.35+fi*0.1)*speedMul;
                float yBase=0.42+fi*0.1;
                float thickness=mix(0.35, 0.24, dark)-fi*0.02;

                vec2 q=vec2(fbm(p*2.2+t*speed),fbm(p*2.2+vec2(1.7,9.2)+t*speed*0.7));
                float f=fbm3(p*1.6+vec2(t*speed*0.5,-t*0.25));

                float curtain=exp(-pow((uv.y-yBase-f*0.2)/thickness,2.0));
                curtain*=0.5+0.5*snoise(vec2(uv.x*3.0+t*speed,uv.y*1.5+t*0.15));
                curtain*=0.7+0.3*snoise(vec2(uv.x*8.0-t*speed*0.5,uv.y*4.0));

                curtain*=smoothstep(0.0,0.1,uv.x)*smoothstep(1.0,0.9,uv.x);
                curtain*=smoothstep(0.12,0.4,uv.y)*smoothstep(1.0,0.68,uv.y);

                // Dark aurora: vivid cyan/green/purple
                vec3 dc1,dc2;
                if(i==0){dc1=vec3(0.0,0.95,0.5);dc2=vec3(0.0,0.6,0.85);}
                else if(i==1){dc1=vec3(0.2,0.7,0.95);dc2=vec3(0.5,0.2,0.95);}
                else if(i==2){dc1=vec3(0.0,0.85,0.6);dc2=vec3(0.0,0.4,0.75);}
                else if(i==3){dc1=vec3(0.25,0.85,0.45);dc2=vec3(0.0,0.65,0.95);}
                else{dc1=vec3(0.35,0.55,0.95);dc2=vec3(0.0,0.95,0.65);}

                // Light aurora: soft pastel lavender/mint/sky
                vec3 lc1,lc2;
                if(i==0){lc1=vec3(0.55,0.75,0.92);lc2=vec3(0.50,0.85,0.75);}
                else if(i==1){lc1=vec3(0.75,0.55,0.88);lc2=vec3(0.55,0.72,0.92);}
                else if(i==2){lc1=vec3(0.50,0.85,0.75);lc2=vec3(0.50,0.65,0.90);}
                else{lc1=vec3(0.68,0.55,0.88);lc2=vec3(0.50,0.85,0.80);}

                vec3 c1=mix(lc1,dc1,dark);
                vec3 c2=mix(lc2,dc2,dark);

                float colorMix=0.5+0.5*sin(uv.x*2.5+t*0.9+fi*1.8);
                vec3 auroraCol=mix(c1,c2,colorMix);

                float brightness=mix(0.4+0.6*(0.5+0.5*sin(uv.x*3.5+t*1.2+fi*0.6)),
                                    0.45+0.55*(0.5+0.5*sin(uv.x*5.0+t*2.0+fi*0.8)), dark);
                curtain*=brightness;
                curtain*=1.0-0.3*abs(uv.x-0.5);

                float contrib=mix(0.7, 0.38, dark);
                col+=auroraCol*curtain*contrib*brightMul;
            }

            // Horizon glow
            float horizon=exp(-pow((uv.y-0.22)/0.3,2.0));
            vec3 hg=mix(vec3(0.88,0.82,0.78), vec3(0.0,0.15,0.1), dark);
            col+=hg*horizon*mix(0.06, 0.3, dark);

            // Mouse glow (dark only)
            float mDist=length((uv-uMouse)*vec2(aspect,1.0));
            float mGlow=exp(-pow(mDist/0.3,2.0))*0.06*dark;
            col+=mix(vec3(0.0,0.75,0.45),vec3(0.25,0.45,0.95),0.5+0.5*sin(t))*mGlow;

            col*=1.0+0.04*sin(t*0.6)*dark;

            // Vignette
            float vig=1.0-mix(0.12,0.35,dark)*pow(length(uv-0.5)*1.2,2.0);
            col*=vig;
            col=clamp(col,0.0,1.0);
            if(dark>0.5) col=pow(col,vec3(0.95));

            gl_FragColor=vec4(col,1.0);
        }
    `;

    const material = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms });
    scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));

    let targetMouse = { x: 0.5, y: 0.5 };
    document.addEventListener('mousemove', e => {
        targetMouse.x = e.clientX / window.innerWidth;
        targetMouse.y = 1.0 - e.clientY / window.innerHeight;
    });

    window.addEventListener('resize', () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
    });

    // Expose method for theme switching
    window.setAuroraTheme = function(isDark) {
        uniforms.uIsDark.value = isDark ? 1.0 : 0.0;
    };

    const clock = new THREE.Clock();
    function animate() {
        requestAnimationFrame(animate);
        uniforms.uTime.value = clock.getElapsedTime();
        uniforms.uMouse.value.x += (targetMouse.x - uniforms.uMouse.value.x) * 0.03;
        uniforms.uMouse.value.y += (targetMouse.y - uniforms.uMouse.value.y) * 0.03;
        renderer.render(scene, camera);
    }
    animate();
})();
