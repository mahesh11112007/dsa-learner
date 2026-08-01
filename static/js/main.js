document.addEventListener('DOMContentLoaded', () => {

  // =============================================
  // Hamburger Mobile Nav Toggle
  // =============================================
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const navMenu = document.getElementById('navMenu');
  if (hamburgerBtn && navMenu) {
    hamburgerBtn.addEventListener('click', () => {
      const isOpen = navMenu.classList.toggle('open');
      hamburgerBtn.classList.toggle('active', isOpen);
      hamburgerBtn.setAttribute('aria-expanded', String(isOpen));
    });
    navMenu.querySelectorAll('.nav-item a').forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('open');
        hamburgerBtn.classList.remove('active');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('click', (e) => {
      if (!hamburgerBtn.contains(e.target) && !navMenu.contains(e.target)) {
        navMenu.classList.remove('open');
        hamburgerBtn.classList.remove('active');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // =============================================
  // Button Ripple Effect
  // =============================================
  document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.className = 'btn-ripple';
      ripple.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size/2}px;top:${e.clientY - rect.top - size/2}px;`;
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // =============================================
  // Dynamic Mouse Glow on Cards
  // =============================================
  document.querySelectorAll('.stat-card,.panel,.feature-card,.plan,.review').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(125,60,255,.14), rgba(17,21,29,.72) 55%)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.background = '';
    });
  });

  // =============================================
  // Scroll Reveal Animation
  // =============================================
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'fadeUp .55s ease forwards';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.stat-card,.panel').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });

  // =============================================
  // File Upload Preview
  // =============================================
  document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const previewId = input.getAttribute('data-preview');
      if (file && previewId) {
        const preview = document.getElementById(previewId);
        if (preview) {
          const reader = new FileReader();
          reader.onload = (evt) => { preview.src = evt.target.result; preview.style.display = 'block'; };
          reader.readAsDataURL(file);
        }
      }
    });
  });

  // =============================================
  // Lightbox Zoom for img-thumb
  // =============================================
  document.querySelectorAll('.img-thumb').forEach(img => {
    img.addEventListener('click', () => {
      const overlay = document.createElement('div');
      Object.assign(overlay.style, {
        position:'fixed',top:'0',left:'0',width:'100vw',height:'100vh',
        backgroundColor:'rgba(13,16,23,.92)',backdropFilter:'blur(14px)',
        zIndex:'2000',display:'flex',flexDirection:'column',
        alignItems:'center',justifyContent:'center',cursor:'zoom-out',padding:'1.5rem'
      });
      const fullImg = document.createElement('img');
      fullImg.src = img.src;
      Object.assign(fullImg.style, {
        maxWidth:'92vw',maxHeight:'85vh',borderRadius:'16px',objectFit:'contain',
        boxShadow:'0 25px 60px rgba(0,0,0,.9),0 0 40px rgba(125,60,255,.3)'
      });
      const caption = document.createElement('p');
      caption.textContent = 'Tap anywhere to close';
      caption.style.cssText = 'color:#64748b;margin-top:1rem;font-size:.9rem;';
      overlay.append(fullImg, caption);
      document.body.appendChild(overlay);
      overlay.addEventListener('click', () => overlay.remove());
    });
  });

  // =============================================
  // Preset Feedback Chips
  // =============================================
  const feedbackTextarea = document.getElementById('feedback');
  document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (!feedbackTextarea) return;
      const text = chip.getAttribute('data-text');
      feedbackTextarea.value = feedbackTextarea.value.trim()
        ? feedbackTextarea.value + '\n' + text
        : text;
    });
  });

  // =============================================
  // Live Search Filter
  // =============================================
  document.querySelectorAll('[data-search-target]').forEach(input => {
    input.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      document.querySelectorAll(input.getAttribute('data-search-target')).forEach(item => {
        item.style.display = item.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  });

  // =============================================
  // Navbar blur on scroll
  // =============================================
  const nav = document.querySelector('.navbar');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.style.background = window.scrollY > 30
        ? 'rgba(13,16,23,.95)'
        : 'rgba(13,16,23,.82)';
    }, { passive: true });
  }

});
