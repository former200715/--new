// NEXUS HOTEL - Soft Aurora Background (Light Mode)
(function() {
    const canvas = document.getElementById('auroraLightCanvas');
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const uniforms = {
        uTime: { value: 0 },
        uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
    };

    const vertexShader = `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position, 1.0); }`;

    // Soft pastel aurora for light theme
    const fragmentShader = `
        precision highp float;
        uniform float uTime;
        uniform vec2 uResolution;
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
            for(int i=0;i<5;i++){f+=w*snoise(p);p*=2.0;w*=0.5;}
            return f;
        }

        void main(){
            vec2 uv=gl_FragCoord.xy/uResolution;
            float aspect=uResolution.x/uResolution.y;
            vec2 p=uv; p.x*=aspect;
            float t=uTime*0.08;

            // Light base - slightly darker so aurora shows
            vec3 col=vec3(0.88, 0.90, 0.93);

            // Subtle floating soft blobs - pastel aurora
            for(int i=0;i<4;i++){
                float fi=float(i);
                float speed=0.12+fi*0.04;
                float yBase=0.5+fi*0.1;
                float thickness=0.35-fi*0.02;

                vec2 q=vec2(fbm(p*1.5+t*speed+fi*2.0),fbm(p*1.5+vec2(3.7,7.3)+t*speed*0.6));
                float f=fbm(p*1.2+q*1.5+vec2(t*speed*0.3,-t*0.1));

                float curtain=exp(-pow((uv.y-yBase-f*0.15)/thickness,2.0));
                curtain*=0.6+0.4*snoise(vec2(uv.x*2.5+t*speed,uv.y*1.2+t*0.1));

                curtain*=smoothstep(0.0,0.15,uv.x)*smoothstep(1.0,0.85,uv.x);
                curtain*=smoothstep(0.15,0.45,uv.y)*smoothstep(1.0,0.7,uv.y);

                // Soft pastel colors: lavender, mint, peach, sky
                vec3 c1,c2;
                if(i==0){c1=vec3(0.62,0.78,0.95);c2=vec3(0.55,0.88,0.78);} // sky -> mint
                else if(i==1){c1=vec3(0.80,0.65,0.92);c2=vec3(0.62,0.78,0.95);} // lavender -> periwinkle
                else if(i==2){c1=vec3(0.55,0.88,0.78);c2=vec3(0.55,0.72,0.92);} // mint -> blue
                else{c1=vec3(0.72,0.65,0.92);c2=vec3(0.55,0.88,0.82);} // lilac -> teal

                float colorMix=0.5+0.5*sin(uv.x*2.0+t*0.5+fi*1.5);
                vec3 auroraCol=mix(c1,c2,colorMix);

                float brightness=0.4+0.6*(0.5+0.5*sin(uv.x*3.5+t*1.2+fi*0.6));
                curtain*=brightness;
                curtain*=1.0-0.25*abs(uv.x-0.5);

                col+=auroraCol*curtain*0.8;
            }

            // Soft warm tint at bottom
            float warm=exp(-pow((uv.y-0.2)/0.4,2.0));
            col+=vec3(0.95,0.88,0.82)*warm*0.08;

            // Very subtle vignette
            float vig=1.0-0.12*pow(length(uv-0.5)*1.2,2.0);
            col*=vig;
            col=clamp(col,0.0,1.0);

            gl_FragColor=vec4(col,1.0);
        }
    `;

    const material = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms });
    scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));

    window.addEventListener('resize', () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
    });

    const clock = new THREE.Clock();
    function animate() {
        requestAnimationFrame(animate);
        uniforms.uTime.value = clock.getElapsedTime();
        renderer.render(scene, camera);
    }
    animate();
})();
