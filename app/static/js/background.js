/**
 * Interactive animated background
 */

class InteractiveBackground {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: 0, y: 0 };
        this.particleCount = 80;
        
        this.setupCanvas();
        this.createParticles();
        this.setupEventListeners();
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
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticles() {
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 2 + 1,
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
            
            // Mouse attraction
            const dx = this.mouse.x - particle.x;
            const dy = this.mouse.y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 150) {
                const force = (150 - distance) / 150;
                particle.vx += dx * force * 0.001;
                particle.vy += dy * force * 0.001;
            }
            
            // Damping
            particle.vx *= 0.99;
            particle.vy *= 0.99;
            
            // Boundary check
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            // Keep in bounds
            particle.x = Math.max(0, Math.min(this.canvas.width, particle.x));
            particle.y = Math.max(0, Math.min(this.canvas.height, particle.y));
            
            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(99, 102, 241, ${particle.opacity})`;
            this.ctx.fill();
            
            // Draw connections
            this.particles.slice(i + 1).forEach(otherParticle => {
                const dx = otherParticle.x - particle.x;
                const dy = otherParticle.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 120) {
                    const opacity = (1 - distance / 120) * 0.3;
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(otherParticle.x, otherParticle.y);
                    this.ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new InteractiveBackground();
});
