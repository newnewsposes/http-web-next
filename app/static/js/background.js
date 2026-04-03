/**
 * Interactive animated background
 */

class InteractiveBackground {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: -9999, y: -9999 };
        this.baseParticleCount = 150; // base max
        this.particleCount = this.baseParticleCount;
        this.connectionDistance = 150;
        this.running = true;
        this.intensity = parseInt(localStorage.getItem('bgIntensity') || '70', 10); // 0-100

        this.mouseNeedsUpdate = false; // for rAF throttling

        this.setupCanvas();
        this.createParticles();
        this.setupEventListeners();
        this.handleVisibility();
        this.animate();
    }
    
    setupCanvas() {
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.zIndex = '-1';
        this.canvas.style.pointerEvents = 'none';
        document.body.prepend(this.canvas);
        
        this.resize();

        // Respect background intensity stored in localStorage
        const intensity = parseInt(localStorage.getItem('bgIntensity') || '70', 10);
        this.particleCount = Math.max(40, Math.floor(this.baseParticleCount * (intensity / 100)));
        this.connectionDistance = 80 + Math.floor(70 * (intensity / 100));
    }
    
    resize() {
        const oldWidth = this.canvas.width;
        const oldHeight = this.canvas.height;
        
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Adjust particle positions on resize to prevent cropping
        if (oldWidth > 0 && oldHeight > 0) {
            const scaleX = this.canvas.width / oldWidth;
            const scaleY = this.canvas.height / oldHeight;
            
            this.particles.forEach(particle => {
                particle.x *= scaleX;
                particle.y *= scaleY;
            });
        }
    }
    
    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * (0.8 + Math.random() * 1.4),
                vy: (Math.random() - 0.5) * (0.8 + Math.random() * 1.4),
                radius: Math.random() * 2 + 0.8,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => this.resize());
        
        document.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
        
        document.addEventListener('touchmove', (e) => {
            if (e.touches.length > 0) {
                this.mouse.x = e.touches[0].clientX;
                this.mouse.y = e.touches[0].clientY;
            }
        });
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        this.particles.forEach((particle, i) => {
            // Move particle
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Mouse attraction (stronger effect)
            const dx = this.mouse.x - particle.x;
            const dy = this.mouse.y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 200) {
                const force = (200 - distance) / 200;
                particle.vx += dx * force * 0.002;
                particle.vy += dy * force * 0.002;
            }
            
            // Less damping = more movement
            particle.vx *= 0.995;
            particle.vy *= 0.995;
            
            // Wrap around edges instead of bouncing
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(99, 102, 241, ${particle.opacity})`;
            this.ctx.fill();
            
                // Draw connections (distance depends on intensity)
            this.particles.slice(i + 1).forEach(otherParticle => {
                const dx = otherParticle.x - particle.x;
                const dy = otherParticle.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.connectionDistance) {
                    const opacity = (1 - distance / this.connectionDistance) * (0.5 * (this.intensity / 100));
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
                    this.ctx.lineWidth = 0.6 * (this.intensity / 100);
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(otherParticle.x, otherParticle.y);
                    this.ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(() => this.animate());
    }

    handleVisibility() {
        document.addEventListener('visibilitychange', () => {
            this.running = !document.hidden;
        });
    }

    setIntensity(value) {
        this.intensity = value;
        localStorage.setItem('bgIntensity', String(value));
        // Recompute particle count and connection distance
        this.particleCount = Math.max(40, Math.floor(this.baseParticleCount * (this.intensity / 100)));
        this.connectionDistance = 80 + Math.floor(70 * (this.intensity / 100));
        this.createParticles();
    }
}

// Expose InteractiveBackground to global so we can lazy-init
window.InteractiveBackground = InteractiveBackground;

// Initialize on page load only if allowed (base file may lazy-load)
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('bgEnabled');
    const allow = saved !== 'false' && !document.body.classList.contains('reduced-motion');
    if (allow) {
        new InteractiveBackground();
    }
});
